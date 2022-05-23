use feature qw(say);
use strict;
use warnings FATAL => 'all';
use MIME::Base64;

sub _b64_encode_int32 {
    my ($value) = @_;
    my $b64 = MIME::Base64::encode(pack("N", $value), "");
    $b64 =~ s/==$//;
    return $b64;
}

sub _b64_decode_int32 {
    my ($b64) = @_;
    $b64 .= "==";
    return unpack "N", MIME::Base64::decode($b64);
}

print(_b64_encode_int32(20000));
