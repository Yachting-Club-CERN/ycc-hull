use feature qw(say);
use strict;
use warnings FATAL => 'all';

# Needs https://metacpan.org/pod/Crypt::PBKDF2
# Source https://metacpan.org/dist/Crypt-PBKDF2/source/lib/Crypt/PBKDF2.pm
use Crypt::PBKDF2;

# Enrico's hashing
my $pbkdf2 = Crypt::PBKDF2->new(
    hash_class => 'HMACSHA1',
    iterations => 20000,
    output_len => 20,
    salt_len   => 16,
);

sub hash_password {
    my ($password) = @_;
    return $pbkdf2->generate($password);
}

sub check_password {
    my ($hash, $password) = @_;
    return $pbkdf2->validate($hash, $password);
}


my $password1 = 'changeit';
my $password2 = 'changeit2';

my $hash1a = hash_password($password1);
my $hash1b = hash_password($password1);
my $hash2 = hash_password($password2);

say($hash1a);
say($hash1b);
say($hash2);

say('Check 1a: ' . check_password($hash1a, $password1));
say('Check 1b: ' . check_password($hash1b, $password1));
say('Check 1 fail: ' . check_password($hash1a, "not good"));

say('Check 2: ' . check_password($hash2, $password2));
say('Check 2 fail: ' . check_password($hash2, "not good"));
