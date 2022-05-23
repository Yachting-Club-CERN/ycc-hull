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

my $hash1 = hash_password($password1);
my $hash2 = hash_password($password1);
my $hash3 = hash_password($password2);
# ~RFC2307
# {X-PBKDF2}HMACSHA1:iterations:salt:hash
my $hash4 = '{X-PBKDF2}HMACSHA1:AABOIA:u1ri6hpMkdJsuzvZ877EJQ==:dee0sA1+RHFxl6Cpw2cFzlYwrwU=';
#my $hash5 = '{X-PBKDF2}HMACSHA1:AABOIA:o6bVpKCmdz4aaJ+g4dkN2g==:bS9NQ1JiMFdta2xaR1RpV1ZSVFR2YWM1bFEw';
my $hash5 = '{X-PBKDF2}HMACSHA1:AABOIA:EYJwTgkhBCDEOIfwvjfmHA==:.Xx9ooGsyr1bTO0VQKnky0O.0Ek=';

say($hash1);
say($hash2);
say($hash3);

say('Check 1: ' . check_password($hash1, $password1));
say('Check 1: ' . check_password($hash2, $password1));
say('Check 1: ' . check_password($hash3, $password1));
say('Check 1: ' . check_password($hash4, $password1));
say('Check 1: ' . check_password($hash5, $password1));

say('Check 2: ' . check_password($hash1, $password2));
say('Check 2: ' . check_password($hash2, $password2));
say('Check 2: ' . check_password($hash3, $password2));
say('Check 2: ' . check_password($hash4, $password2));
say('Check 2: ' . check_password($hash5, $password2));

say('Check: '.check_password('{X-PBKDF2}HMACSHA1:AABOIA:rLWWsjaG8N5bq7WWMiZkjA:ZwKlB5rKotPeWUvQx6dmOMD/WdU', 'changeit'));