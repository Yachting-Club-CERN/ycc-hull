sub BUILD {
  my ($self) = @_;
  $self->hasher; # Force instantiation, so we get errors ASAP
}


has hasher => (
  is => 'ro',
  isa => ConsumerOf['Crypt::PBKDF2::Hash'],
  lazy => 1,
  default => sub { shift->_lazy_hasher },
);

has _lazy_hasher => (
  is => 'ro',
  isa => ConsumerOf['Crypt::PBKDF2::Hash'],
  lazy => 1,
  init_arg => undef,
  predicate => 'has_lazy_hasher',
  builder => '_build_hasher',
);

sub _build_hasher {
  my ($self) = @_;
  my $class = $self->hash_class;
  if ($class !~ s/^\+//) {
    $class = "Crypt::PBKDF2::Hash::$class";
  }
  my $hash_args = $self->hash_args;

  return Module::Runtime::use_module($class)->new( %$hash_args );
}


has iterations => (
  is => 'ro',
  isa => Int,
  default => 1000,
);


has output_len => (
  is => 'ro',
  isa => Int,
  predicate => 'has_output_len',
);


has salt_len => (
  is => 'ro',
  isa => Int,
  default => 4,
);

sub _random_salt {
  my ($self) = @_;
  my $ret = "";
  for my $n (1 .. $self->salt_len) {
    $ret .= chr(int rand 256);
  }
  return $ret;
}


has encoding => (
  is => 'ro',
  isa => Str,
  default => 'ldap',
);


has length_limit => (
  is => 'ro',
  isa => Int,
  predicate => 'has_length_limit',
);


sub generate {
  my ($self, $password, $salt) = @_;
  $salt = $self->_random_salt unless defined $salt;

  if ($self->has_length_limit and length($password) > $self->length_limit) {
    croak "Password exceeds length limit";
  }

  my $hash = $self->PBKDF2($salt, $password);
  return $self->encode_string($salt, $hash);
}


sub validate {
  my ($self, $hashed, $password) = @_;

  if ($self->has_length_limit and length($password) > $self->length_limit) {
    croak "Password exceeds length limit";
  }

  my $info = $self->decode_string($hashed);

  my $hasher = try {
    $self->hasher_from_algorithm($info->{algorithm}, $info->{algorithm_options});
  } catch {
    my $opts = defined($info->{algorithm_options}) ? " (options ''$info->{algorithm_options}'')" : "";
    croak "Couldn't construct hasher for ''$info->{algorithm}''$opts: $_";
  };

  my $checker = $self->clone(
    hasher => $hasher,
    iterations => $info->{iterations},
    output_len => length($info->{hash}),
  );

  my $check_hash = $checker->PBKDF2($info->{salt}, $password);

  return ($check_hash eq $info->{hash});
}


sub PBKDF2 {
  my ($self, $salt, $password) = @_;
  my $iterations = $self->iterations;
  my $hasher = $self->hasher;
  my $output_len = $self->output_len || $hasher->hash_len;

  my $hLen = $hasher->hash_len;
  my $l = int($output_len / $hLen);
  my $r = $output_len % $hLen;

  if ($l > 0xffffffff or $l == 0xffffffff && $r > 0) {
    croak "output_len too large for PBKDF2";
  }

  my $output;

  for my $i (1 .. $l) {
    $output .= $self->_PBKDF2_F($hasher, $salt, $password, $iterations, $i);
  }

  if ($r) {
    $output .= substr( $self->_PBKDF2_F($hasher, $salt, $password, $iterations, $l + 1), 0, $r);
  }

  return $output;
}


sub PBKDF2_base64 {
  my $self = shift;

  return MIME::Base64::encode( $self->PBKDF2(@_), "" );
}


sub PBKDF2_hex {
  my $self = shift;
  return unpack "H*", $self->PBKDF2(@_);
}

sub _PBKDF2_F {
  my ($self, $hasher, $salt, $password, $iterations, $i) = @_;
  my $result =
  my $hash =
    $hasher->generate( $salt . pack("N", $i), $password );

  for my $iter (2 .. $iterations) {
    $hash = $hasher->generate( $hash, $password );
    $result ^= $hash;
  }

  return $result;
}


sub encode_string {
  my ($self, $salt, $hash) = @_;
  if ($self->encoding eq 'crypt') {
    return $self->_encode_string_cryptlike($salt, $hash);
  } elsif ($self->encoding eq 'ldap') {
    return $self->_encode_string_ldaplike($salt, $hash);
  } else {
    die "Unknown setting '", $self->encoding, "' for encoding";
  }
}

sub _encode_string_cryptlike {
  my ($self, $salt, $hash) = @_;
  my $hasher = $self->hasher;
  my $hasher_class = blessed($hasher);
  if (!defined $hasher_class || $hasher_class !~ s/^Crypt::PBKDF2::Hash:://) {
    croak "Can't ''encode_string'' with a hasher class outside of Crypt::PBKDF2::Hash::*";
  }

  my $algo_string = $hasher->to_algo_string;
  $algo_string = defined($algo_string) ? "{$algo_string}" : "";

  return '$PBKDF2$' . "$hasher_class$algo_string:" . $self->iterations . ':'
  . MIME::Base64::encode($salt, "") . '$'
  . MIME::Base64::encode($hash, "");
}

sub _encode_string_ldaplike {
  my ($self, $salt, $hash) = @_;
  my $hasher = $self->hasher;
  my $hasher_class = blessed($hasher);
  if (!defined $hasher_class || $hasher_class !~ s/^Crypt::PBKDF2::Hash:://) {
    croak "Can't ''encode_string'' with a hasher class outside of Crypt::PBKDF2::Hash::*";
  }

  my $algo_string = $hasher->to_algo_string;
  $algo_string = defined($algo_string) ? "+$algo_string" : "";

  return '{X-PBKDF2}' . "$hasher_class$algo_string:"
  . $self->_b64_encode_int32($self->iterations) . ':'
  . MIME::Base64::encode($salt, "") . ':'
  . MIME::Base64::encode($hash, "");
}


sub decode_string {
  my ($self, $hashed) = @_;
  if ($hashed =~ /^\$PBKDF2\$/) {
    return $self->_decode_string_cryptlike($hashed);
  } elsif ($hashed =~ /^\{X-PBKDF2}/i) {
    return $self->_decode_string_ldaplike($hashed);
  } else {
    croak "Unrecognized hash";
  }
}

sub _decode_string_cryptlike {
  my ($self, $hashed) = @_;
  if ($hashed !~ /^\$PBKDF2\$/) {
    croak "Unrecognized hash";
  }

  if (my ($algorithm, $opts, $iterations, $salt, $hash) = $hashed =~
      /^\$PBKDF2\$([^:}]+)(?:\{([^}]+)\})?:(\d+):([^\$]+)\$(.*)/) {
    return {
      algorithm => $algorithm,
      algorithm_options => $opts,
      iterations => $iterations,
      salt => MIME::Base64::decode($salt),
      hash => MIME::Base64::decode($hash),
    }
  } else {
    croak "Invalid format";
  }
}

sub _decode_string_ldaplike {
  my ($self, $hashed) = @_;
  if ($hashed !~ /^\{X-PBKDF2}/i) {
    croak "Unrecognized hash";
  }

  if (my ($algo_str, $iterations, $salt, $hash) = $hashed =~
      /^\{X-PBKDF2}([^:]+):([^:]{6}):([^\$]+):(.*)/i) {
    my ($algorithm, $opts) = split /\+/, $algo_str;
    return {
      algorithm => $algorithm,
      algorithm_options => $opts,
      iterations => $self->_b64_decode_int32($iterations),
      salt => MIME::Base64::decode($salt),
      hash => MIME::Base64::decode($hash),
    }
  } else {
    croak "Invalid format";
  }
}


sub hasher_from_algorithm {
  my ($self, $algorithm, $args) = @_;
  my $class = Module::Runtime::use_module("Crypt::PBKDF2::Hash::$algorithm");

  if (defined $args) {
    return $class->from_algo_string($args);
  } else {
    return $class->new;
  }
}


sub clone {
  my ($self, %params) = @_;
  my $class = ref $self;

  # If the hasher was built from hash_class and hash_args, then omit it from
  # the clone. But if it was set by the user, then we need to copy it. We're
  # assuming that the hasher has no state, so it doesn't need a deep clone.
  # This is true of all of the ones that I'm shipping, but if it's not true for
  # you, let me know.

  my %new_args = (
    $self->has_hash_class  ? (hash_class  => $self->hash_class) : (),
    $self->has_hash_args   ? (hash_args   => $self->hash_args)  : (),
    $self->has_output_len  ? (output_len  => $self->output_len) : (),
    $self->has_lazy_hasher ? () : (hasher => $self->hasher),
    iterations => $self->iterations,
    salt_len => $self->salt_len,
    %params,
  );

  return $class->new(%new_args);
}

sub _b64_encode_int32 {
  my ($self, $value) = @_;
  my $b64 = MIME::Base64::encode(pack("N", $value), "");
  $b64 =~ s/==$//;
  return $b64;
}

sub _b64_decode_int32 {
  my ($self, $b64) = @_;
  $b64 .= "==";
  return unpack "N", MIME::Base64::decode($b64);
}