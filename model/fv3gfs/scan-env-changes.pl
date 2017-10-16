#! /usr/bin/env perl

use strict;
use warnings;

sub readit {
    my $file=$_[0];
    open(CFG,"$file") or die "$file";
    my @lines=<CFG>;
    close(CFG);
    my %vars;
    foreach (@lines) {
        chomp;
        /^BASH_/ and next;
        /^([A-Za-z][A-Za-z0-9_]+)=(.*)/ or next;
        $vars{$1}=$2;
    }
    return %vars;
}

sub diffmod {
    my %before=%{$_[0]};
    my %after=%{$_[1]};
    my %before_env=%{$_[2]};
    my %after_env=%{$_[3]};

    foreach my $name (sort {$a cmp $b} keys(%before)) {
        if(!defined($after{$name})) {
            print("unset $name\n");
            next;
        }

        if(defined($before_env{$name}) && !defined($after_env{$name})) {
            print("export -n $name\n");
        }

        if($before{$name} ne $after{$name}) {
            if(defined($after_env{$name})) {
                print("export $name=\"$after{$name}\"\n");
            } else {
                print("$name=\"$after{$name}\"   # shell-local\n");
            }
        } elsif(!defined($before_env{$name}) && defined($after_env{$name})) {
            print("export $name\n");
        }
    }

    foreach my $name (sort {$a cmp $b} keys(%after)) {
        if(!defined($before{$name})) {
            if(defined($after_env{$name})) {
                print("export $name=\"$after{$name}\"\n");
            } else {
                print("$name=\"$after{$name}\"   # shell-local\n");
            }
        }
    }
}

########################################################################

my $pre=$ARGV[0];

print("# checkit.pl $pre\n");

my %before_set=readit("$pre\%set\%before-to-sh");
my %after_set=readit("$pre\%set\%after-to-sh");

my %before_env=readit("$pre\%env\%before-to-sh");
my %after_env=readit("$pre\%env\%after-to-sh");

print("# Variable changes:\n");
diffmod(\%before_set,\%after_set,\%before_env,\%after_env)
