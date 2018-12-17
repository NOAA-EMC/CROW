# This is a grammar file used by the textgen.pl program, based on Sam
# Trahan's insult engine.  That program is essentially a recursive
# madlib program: it takes a list of rules and uses them to generate
# human-readable text, as explained below.

# Lines beginning with a double dash and a space ("-- ") declare a new
# "terminal" whose name is immediately after the space.  Each terminal
# definition is followed by a list of rules that explain how the
# terminal can be expanded into multiple other terminals, or into raw
# text.  Text in parenthases indicates that the terminal whose name is
# in the parenthases should be expanded.  The parser (textgen.pl)
# starts from one particular terminal, and expands that terminal until
# there are no more terminal expansions to do.  So, with a starting
# terminal of CAT, this:
#
# -- CAT
# (C) are (T)
#
# -- C
# cows
#
# -- T
# tasty
#
# would expand to "cows are tasty".  You can have more than one
# rule for a terminal:
# 
# -- CAT
# (C) are (T)
# 
# -- C
# cows
# bovine animals
# calves
#
# -- T
# tasty
# delicious
#
# That would end up being expanded at random into any of these:
#
#   - calves are tasty
#   - calves are delicious
#   - cows are tasty
#   - cows are delicious
#   - bovine animals are tasty
#   - bovine animals are delicious
#
# You can instruct the parser to never use a rule more than once using this command:
#
# @single C
#
# With that command, any time the rule for the terminal "C" is expanded, the rule is
# discarded, so that it won't be used again.  That feature is intended to be used
# to prevent the parser from using a word more than once, hence preventing output
# like "the sky is very blue, clear, windy, blue and blue today".
#
# There are other strings that have special meanings to the parser:
#
# %n = end of line
# %_ = space (otherwise, duplicate spaces are removed)
# %0 = first argument to script after the grammar file, %1 = second, etc.
# %< = insert a begin parethases (
# %> = insert an end parenthases )
# %% = insert a percent sign
#
# Also, recursive rules are okay:
#
# -- you are ugly
# you are very(, very) ugly
#
# -- , very
# (, very), very
# , very
#
# Starting from the "you are ugly" terminal, that will expand into "you are very"
# followed by the text ", very" repeated one or more times, followed by "ugly".
#
# Also, you can use this syntax:
#
# -- you smell
# you smell[ very] bad
#
# To indicate that the string " very" can optionally (with 50% chance) be inserted
# between "smell" and "bad".  You cannot nest those braces though, so no [ very[, very]]
# However, you can place a terminal expansion in the braces like this:
#
# -- you are ugly
# you are very[(, very)] ugly
#
# -- , very
# (, very), very
# , very
#
# Which differs from our previous "you are ugly" example in that the
# ", very" is repeated *zero* or more times since it is now nested in [] in the
# "you are ugly" rule.

########################################################################
########################################################################

-- *
(INTRO AND SIG)

-- INTRO AND SIG
(INTRO)%n%n%2%n%n(SIGNATURE)%n%n%4%n

-- FAILED INTRO AND SIG
(FAIL INTRO)%n%n%2%n%n(FAILED SIG)%n%n%4%n

-- RECHECK INTRO AND SIG
(RECHECK INTRO)%n%n%2%n%n(RECHECK SIG)%n%n%4%n

-- ME
CROW's Bird-Sitter

-- INTRO
(GREETING,)%n%n(HELLO! I AM CROW) (COLOR) (EXCUSES AND APOLOGY FOR ISSUES)%n%n(HERE IS THE STATUS)

-- SIGNATURE
(PEACE OUT, MAN)%n%_-(ME) for %0%n%n(DON'T SUE ME: NO FAILURES)

-- FAIL INTRO
(GREETING,)%n%n(PANIC!PANIC!)(I AM A SAD CROW)(I AM REALLY SORRY, BUT A SIMULATION FAILED)(I CANNOT FIX IT)(PLEASE DO NOT HATE ME)%n%n(HERE IS THE STATUS, NO JOKES)

-- RECHECK INTRO
(GREETING,)%n%n(I AM AN CROW THAT RECHECKED STUFF)%n%n(HERE IS THE RECHECKED STATUS)

-- FAILED SIG
(APOLOGETIC PEACE OUT, MAN)%n%_-(ME) for %0%n%n(DON'T SUE ME: FAILURES)

-- RECHECK SIG
(APOLOGETIC PEACE OUT, MAN)%n%_-(ME) for %0%n%n(DON'T SUE ME: RECHECK)

-- DON'T SUE ME: FAILURES
This is an automatically-generated 1960s hippie-themed email about ERRORS from (ME) on %3 for configuration "%0" running "%1."

-- DON'T SUE ME: RECHECK
This is an automatically-generated 1960s hippie-themed email about A STATUS RECHECK from (ME) on %3 for configuration "%0" running "%1."

-- DON'T SUE ME: NO FAILURES
This is an automatically-generated 1960s hippie-themed status email from (ME) on %3 for configuration "%0" running "%1."

-- I AM AN CROW THAT RECHECKED STUFF
(Rechecked)!!%_[ (Wow!)%_] (I am CROW running fv3.) (It is) (working correctly)[ now](.!)[ (Wow!)%_]
(Rechecked)!!%_ (I am CROW running fv3.) 
(I am CROW running fv3.) (Dude), I have (soooo) (rechecked) these (simulations)(.!)%_ Nothing (broken) yet...%_
(I am CROW running fv3.) I have (rechecked) your (simulations), (dude).%_ Nothing (broken) yet...%_

-- OKAY BUT I WARNED YOU
(Y'know) (dude), (I'll do it), but (I did warn you)...

-- I'll do it
I'll do it
I'll mark it
I will

-- I did warn you
I did warn you
I warned you
don't blame me when this breaks (something)

-- BYE
(ASCII ART)
(Peace out)[, man](.!)%_
(Peace out)[, chick](.!)%_
Later, (dude)(.!)%_

-- ASCII ART
%<-:
8-P
0-:
:-%>
%<^_^%>
%<o_o%>
%<x_x%>
%<o_O%>

-- RECHECK INSTEAD
(Dude), (something probably broke).%_ (You should really run recheck-cycles.bash instead).%_  (Are you sure you want to) mark this FAILURE_OKAY %<y/N%>?%_ 

-- Are you sure you want to
Are y'sure you want me to
Are y'sure you want me to
Are you sure you want me to
Are you sure you want me to
Are you sure you want me to
Sure you wanna
Y'sure you wanna

-- Sorry about breaking this
(I am)[ (soooo)] sorry about [(scapegoat) ][(flaking out) and ](breaking) your[ (complimented)] (simulations)
(I am)[ (soooo)] sorry about [(scapegoat) ][(flaking out) and ](breaking) this
(I am)[ (soooo)] sorry about [(scapegoat) ](breaking) this
(I am)[ (soooo)] sorry that (I or scapegoat) [(flaked out) and ](broke) your[ (complimented)] (simulations)
(I am)[ (soooo)] sorry that (I or scapegoat) [(flaked out) and ](broke) this
(I am)[ (soooo)] sorry that (I or scapegoat) (broke) this

-- I or scapegoat
(scapegoat)
I
I

-- something probably broke
either the (simulations) failed or I'm (configured wrong)

-- You should really run recheck-cycles.bash instead
You should (fix the problem) and (run) recheck-cycles.bash instead

-- fix the problem
fix the problem
correct it
fix it
correct the problem

-- configured wrong
configured wrong
configured incorrectly
misconfigured

-- HELLO! I AM CROW
[(Dude babbling.) ](I am CROW running fv3.)

-- I AM A SAD CROW
(I am badly running) %0(, okay?)
(Uhhhh... I am) (ME)(, and stuff.) (I am badly running) %0(, okay?)
(Uhhhh... I am) (ME), (badly running) %0(, okay?)

-- PANIC!PANIC!
Help! HELP!!!%_
HELP!!%_
ERRORS!!%_
Please help!!%_
You are SO going to kill me!!%_
OHNO!!%_
Wipe out!%_
Zilch, man.%_

-- I AM REALLY SORRY, BUT A SIMULATION FAILED
I was (trying to beat) (competitor model) but I (broke) (your simulations),%_
I (flaked out) and (broke) (your simulations).%_
I (broke) (your simulations).%_
(I know I said I would not) (flake out), (but I did.)%_ I (broke) (your simulations).%_
(So sorry, but), I [(kinda) ](broke) (your simulations).%_

-- HERE IS THE RECHECKED STATUS
(Dude), (here it is):
(Here it is):
(Wow!)
I didn't (flake out) this time:
I didn't (break) the (simulations) this time:
(I won't) (flake out) again:
(I won't) (break) these again:

-- PLEASE DO NOT HATE ME
(Blame Sam.)
(Blame Sam.)
(Blame Sam.)
(Blame Sam.)
(This sucks.)
(Don't have a cow.)
(Don't have a cow.) (Killing me won't fix it.)
Please don't tell (an authority).%_ (I am still in trouble from) (past crimes).%_
Please don't tell (an authority).%_ (I am still in trouble from) (past crimes).%_
Please don't tell (an authority).%_ (I am still in trouble from) (past crimes).%_
Please don't tell (an authority).%_ (I am still in trouble from) (past crimes).%_

-- part of NOAA
GFDL
ESRL
NOAA HQ
EMC
the NCEP Director
Security

-- an authority
(the cops)
(the cops)
(the cops)
(the government)
(part of NOAA)
(part of NOAA)

-- I CANNOT FIX IT
(I am)[ like], (way too much of an idiot) (to fix this).%_

-- EXCUSES AND APOLOGY FOR ISSUES
(I'll try not to) (flake out later)[, (but you know how I can be)](.!)%_

-- GREETING,
Dear (dude)(,,:)
(Dude)(,,:)

-- PEACE OUT, MAN
(Peace out)[, man](.!)%_
(Peace out)[, chick](.!)%_
Later, (dude)(.!)%_
(Wow!)
(ASCII ART)

-- Peace out
Peace out
Peace out
Fight the power
Keep fightin' the power
Peace
Peace
Down with the establishment
Fight The Man
Flower power
Deuce
Be (good)

-- APOLOGETIC PEACE OUT, MAN
(Peace out)[, man](.!)%_
(Peace out)[, chick](.!)%_
Sorry, (dude)(.!)%_
Sorry, (dude)(.!)%_
Sorry, (dude)(.!)%_

-- COLOR
(I am) (high and/or distracted)(.!)
(Dude), these are (complimented) (simulations)(.!)
(Dude), your (simulations) are (complimented)(.!)
This is[, like], [(soooo) ](fun)[, (dude)](.!)
(I am) (having a blast)!
(Wow!)

-- HERE IS THE STATUS, NO JOKES
(Soooo) sorry, but, here is what I (broke):
(Soooo) sorry, but, here is what I (broke):
(Soooo) sorry, but, here is what I (broke):
(Soooo) sorry, but, here is what I (broke):
Yup.  I'm sure (scapegoat) caused this:
This is probably (scapegoat)'s fault somehow, not mine:
(Get angry at user:)

-- HERE IS THE STATUS
(Okay), (right)(.!)%_ You want (the real stuff), (and I got that):
(Okay), (right)(.!)%_ You want (this stuff):
(Okay), (right)(.!)%_ You want (this stuff):
(Okay), (right)(.!)%_ You want (this stuff):
(Okay), (right)(.!)%_ (You want the dig, I got the dig):
(Bizarre nonsense...)

-- competitor model
ECMWF
ECMWF
ECMWF
the official forecast
HWRF
climatology

-- trying to beat
trying to beat
trying to beat
racing them
bookin' to
burnin' rubber like
peelin' out to
toolin' to
truckin' to

-- here it is
here it is
here it be
here
lookit this
look here

-- Here it is
Here it is
Here it be
Here
Lookit this
Look here

-- I won't
I won't
I won't
I wont
I'm not gonna


-- It is
It's
It's
It's
It's, like
It's, y'know
It's, like
It's, y'know
It is
It is, like
It is, y'know

-- Rechecked
Rechecked
Rechecked
Rechecked
Recheck'd
Recheck'd
Recheckened
Rechickened
Recheckered

-- rechecked
rechecked
rechecked
rechecked
recheck'd
recheck'd
rechickened
recheckened
recheckered

-- working correctly
a gas
having a ball
working
drawin[g] designs
fab
far out
outta sight
on the make
at the pad
righteous
a real gone cat

-- You want the dig, I got the dig
You want the dig, I got the dig
You want the good stuff, I got the good stuff
You want the church key, I got the church key
You want the real stuff, I got the real stuff
You want the brew, I got the brew
Here's your midnight auto supply
Here's your five-finger discount
Peel out to this
Kings X

-- Bizarre nonsense...
(Jinx)!%_ You owe me (a coke)!%_ (Just kidding.) Anyway...
Meanwhile, back at the ranch...
(Dibs) on (the property).
Chickabiddy.

-- Dibs
Dibs

-- the property
the cobs
the brody knob
the brew
the scratch
the shades
the threads
the peggers
the pawdiddle
the pad

-- the real stuff
the good stuff
the real stuff
the blitz
the real brew
the church key
the crash
the cherry stuff

-- and I got that
and I got that
so here it is[ (complimented) (dude)]
and here it is

-- Okay
Okay
So
Yea[h]

-- right
right
okay

-- kinda
[like, ]kinda[, y'know,%_]
[like, ]sorta[, y'know,%_]
like,
kinda
sorta
sort of
kind of
kinda-sorta,

-- your simulations
your (simulations)
the (simulations)
some (simulations)

-- broke
skuzzed up
screwed up
crashed
blew the doors off
jacked up
jammed
jinxed
kiboshed
put the kibosh on
pantsed
raked
pounded
scarfed
scratched up
shorted
broke

-- broke
skuzzed up
screwed up
crashed
blown
jacked up
jammed
jinxed
kiboshed
kiboshed
pantsed
raked
pounded
scarfed
scratched up
shorted
broken

-- but I did.
but I did.
but I did.
but, you know...
but you know me[ better than that].[..]

-- this stuff
this stuff
these things
stuff and things
the dig
the dig
the good stuff

-- So anyway
Right, so anyway
So anyway
And, uh, right

-- fun
fun
# FIXME: need more here

-- having a blast
having a ball
burning rubber
like, choice right now
like, decked out
[(soooo) ](digging) this
(soooo) (happy)

-- digging
digging
scarfing
ruling

-- happy
hip
hep
jazzed
outta sight

-- I am
I'm
I'm
I'm
I am
I am, like
I'm, like

-- I know I said I would not
I know said I (would not)
I (kinda) said I (would not)

-- This sucks.
What a bummer.%_
I am so bummed out now.%_
I am such a (complimented) (dude), so it must be (someone else's) fault.
It was probably cosmic rays hitting %3 again.%_
(I am) sure it was my bad karma.%_
(I am) sure it was %3's bad karma.%_
I'm gonna lay rubber now...

-- someone else's
someone else's
Sam's
Sam's
Sam's
Terry's
Kate's
Jian's
Lin's
Bin's
Rich's
Vijay's
your
(the police's)
(the government's)

-- the police's
the pigs'
the heat's
the police's
heat's
fuzz's

-- the government's
the gov'ment's
the gov'ment's
the gov'ment's
the government's
Uncle Sam's

-- the government
the gov'ment
the gov'ment
the gov'ment
the government
Uncle Sam

-- I am still in trouble from
(I am) still in trouble from
They're still after me from
They still want me for

-- past crimes
(simulation issues)
breaking your other (simulations)
breaking (other person)'s (simulations)
(bringing down) (resource)
(bringing down) (resource)

-- bringing down
bringing down
breaking
crashing
screwing up

-- breaks
breaks
crashes
screws up

-- resource
(a cluster)
(a cluster)
(a filesystem)
(a filesystem)
(another resource)

-- a cluster
Jet
Surge
Luna
Theia
Gyre
Tide
Cheyenne
Yellowstone
GAEA

-- a filesystem
GPFS
HPSS
MSS
the filesystems
ptmp
glade
hps2
hps3
hps
stmp
scratch3
scratch4
lfs3
lfs1
lfs2
pan2
SSS

-- another resource
LoadLeveler
the network
the Infiniband switches
the queue manager
Rocoto
ecFlow
(sun grid engine)
weather.gov
AWIPS

-- sun grid engine
SGE
SGE
Oracle Grid Engine
Sun Grid Engine

-- specific scapegoat
Sam
Sam
Sam
Sam
Moorthi
Moorthi
Moorthi
Vijay
Terry
Rich
Kate
Jian
Bin
Lin
Rahul
Fanglin

-- generic scapegoat
someone else
some other jerk

-- scapegoat
(specific scapegoat)
(specific scapegoat)
(specific scapegoat)
(specific scapegoat)
(generic scapegoat)

-- Get angry at user:
(No, wait, if) you are (going to) blame me, then (fix it yourself!)

-- No, wait, if
No, (wait), if
(Wait)(.!) If

-- Wait
Wait
Wait a minute
Hey
Hay

-- wait
wait
wait a minute
hey
hay

-- climb it, Tarzan
climb it, Tarzan!
climb it, Tarzan!
have a gas with a bass!
bench race yourself!
brody to a pot hole!

-- fix it yourself!
[ you can] [climb it, Tarzan!]%_ Fix it yourself:
fix it yourself[, jerk]!
maybe I won't email you any more!

-- Person's
(other person)'s

-- other person
Sam
Sam
Sam
Kate
Rich
Terry
Lin
Bin
Vijay
Fanglin
Rahul
Moorthi

-- simulation issues
the warm stratospheric temperatures
the weak stratospheric jets
the high RMSE for winds in the tropics
land surface bias trouble
diffusion-induced widening of TCs
the overabundance of high clouds

-- Don't have a cow.
But don't have a cow[, (dude)](.!)%_
But don't flip your wig[, (dude)](.!)%_
Please don't hurt me.%_
Hang loose and fix it, (dude).%_
Just hang loose and fix it, (dude).%_

-- Killing me won't fix it.
Killing me won't fix it.%_
Killing me won't get these running[ again].%_
Killing me won't get you anywhere.%_

-- way too much of an idiot
too much of (an idiot)
too (stupid)

-- an idiot
a spaz
a nerd
an idiot
a winnie
a sweat hog
a skuzz
a panty-waist

-- stupid
blitzed
loaded
stupid
useless
skuzz

-- going to
going to
gonna
gonna

-- the cops
the (cops)

-- cops
cops
pigs
heat
police
fuzz

-- to fix this
to fix this
to do anything now
to bag this

-- Blame Sam.
(It was probably) (Person's) fault.%_
(It was probably) (Person's) fault.%_
(other person) made me do it.%_
I wanted it to work but (Sam made me break it).%_
I wanted it to work but (Sam made it too complicated).%_

-- Klingon
Klingon
Klingon
Klingon
Goa'uld
Goa'uld
Poliespo
Sindarin
Newspeak
Newspeak
Furbish
Bidjara
Sanskrit

-- Sam made it too complicated
(specific scapegoat) made it too complicated
(specific scapegoat) made it so hard all I could do was cry
(specific scapegoat) didn't document it at all
(specific scapegoat) only documented it in (Klingon) 
(specific scapegoat) never answers emails

-- Sam made me break it
(specific scapegoat) made me break it
(specific scapegoat) broke it
(specific scapegoat) screwed it up

-- It was probably
Probabaly was
M' sure it was
It was 

-- would not
would not
would, like, not
wouldn't
wouldn't
wouldn't

-- So sorry, but
(I am)[ (soooo)] sorry, but
(Soooo) sorry, but
Sorry, but

-- I'll try not to
I'll try not to
I'll really try not to
I'll, like, try not to

-- but you know how I can be
but you know how I am
but you know I'm a (naughty) (loser)
but you know I'm a (bad person)
but you know I'm a (bad person)

-- naughty
blitzed
ditzy
heavy
old
panty-waist
flaky
pigged-out
stoned
zitty

-- loser
dork
drag
spaz[z]
square
hodad
chrome dome
dip stick

-- bad person
sweat hog
panty-waist
flake
dork
drag
spaz[z]
dork
square
chrome dome
dip stick
ditz

-- flake out later
(break) these
(flake out) later
(flake out) when running these

-- flaking out
beating feet
blowing the doors off
bugging out
flaking[ out]
flaking[ off]
chickening out
being a drag
wigging out
wiping out
all show and no go
bench racing
catching some rays
deucing with a goose
racing for pinks
peeling outta my pad
at the submarine races

-- flake out
beat feet
blow the doors off
bug out
flake[ out]
flake[ off]
chicken out
be a drag
wig out
wipe out
bench race
catch some rays
deuce with a goose
race for pinks
peel outta my pad
be at the submarine races

-- flaked out
beat feet
blew the doors off
bugged out
flaked[ out]
flaked[ off]
chickened out
dragged
wigged out
wiped out

-- break
blow the doors off
skuzz[ up]
ape
boogie
brody
freak out
jam
pound
split

-- breaking
blowing the doors off
skuzzing[ up]
aping
boogying
brodying
freaking out
jamming
pounding
splitting

-- broken
blew the doors off
skuzzed[ up]
aped
boogied
brodied
freaked out
jammed
pounded
split

-- simulations
simulations
simulations
sim'lations
simulations
sim'lations
FV3s
runs
forecasts
`casts
cycles

-- I am CROW running fv3.
(I am, like,) (ME)(, and stuff.)(I am running) %0(, okay?)
(I am, like,) (ME)(, okay?)(I am running) %0(, and stuff.)
(I am, like,) (ME), (running) %0(, okay?)
(I am, like,) (ME), (running) %0(, and stuff.)
(I am) (ME)(, and stuff.) (I am running) %0(, okay?)
(I am) (ME), (like, you know, running) %0(, okay?)
(I am) (ME), (like, you know, running) %0(, and stuff.)

-- Dude babbling.
(Dude)(.!?)
(Complimented) (dude)(.!?)
(So,) [(complimented) ](dude)(.?)
(You are)[, like,] (amazing), (dude)!%_
(You are)[, like,] (amazing), (dude).%_

-- So,
So,
Hey there,
Hey, you

-- Uhhhh... I am
(Uhhhh...) I am
(Y'know), so, 

-- I am, like,
I am
I am, like,
I am, (y'know),
(Y'know), I am
(Y'know) I am, like, 

-- I am running
I am (running)
I'm (running)

-- I am badly running
I am (badly running)
I'm (badly running)

-- like, you know, running
(running)
like, (running)
(y'know), (running)
like, (y'know), (running)
(y'know), like, (running)

-- something
something
something
somethin'
somethin'

-- , or something
, or (something)

-- Jinx
Jinx
Jinx
Pawdiddle
Pawdunkle

-- a coke
a coke
a pepsi
a beer
a dollar

-- Just kidding.
Just kidding.%_
Just kidding.%_
Just joking.%_
Kidding!%_ Kidding!%_

-- Wow!
(Nonsensical exclamation!)
(Nonsensical exclamation!)
(Nonsensical exclamation!)
(Good!)
(Good!)
(Good!)
What (a party)[!]!%_
What (a party)[!]!%_
What (a party)[!]!%_
What (a party)[!]!%_

-- Good!
Deuce![!]%_
Fab![!]%_
Far out![!]%_
Twitchin'%_
Kings X![!]%_
Boss![!]!%_
Way out![!]%_

-- good
deuce
fab
far out
twitchin'
boss
way out

-- Nonsensical exclamation!
Pawdiddle![!]%_
Pawdunkle![!]%_
Wow![!]%_
Wow![!]%_
Wooooooo![!!]%_
Wooooooo![!!]%_
Yeaaah!![!!!]%_
Yeaaah!![!!!]%_

-- a party
a gas
a blast
a jam
a party

-- high and/or distracted
having a good time
copasetic
cruising
digging this
funky

-- , okay?
.%_
.%_
!%_
, (y'know)?%_
, okay?%_
, `kay?%_
, chickabiddy?%_

-- amazing
(complimented)
(complimented)
(soooo) (complimented)

-- soooo
so
soooo
soooooo
like, really
really

-- Soooo
So
Soooo
Soooooo
Like, really
Really

-- , and stuff.
, and (stuff).%_
, (dude).%_
(, or something).%_
[(, or something)], (y'know)?%_

-- y'know
right
okay
`kay
y'know

-- Y'know
Right
Okay
Y'know

-- stuff
things
stuff
stuff

-- run
run
use

-- running
running
runin'
doing, like
doin' some
spinnin' some cycles of
doin' some fine

-- badly running
(badly) running
(badly) runin'
doin' a (bad) job of running
doin' a (bad) job of runnin'

-- Uhhhh...
Uhhhh...
Um...
So...
Right...
Right, so...
Y'know...
Okay, so...

-- .!
.%_
!%_

-- .?
.%_
?%_

-- .!?
.%_
!%_
?%_

-- badly
badly
scuzzingly
raunchily
suckily

-- bad
bad
scuzzed-up
scuzzy
drag
raunchy
sucky

-- You are
You are
You're
You are
You're
Y'know, you are
Y'know, you're
You're, like
Y'know, you're, like
You're, like, y'know

-- Complimented
Cool
Ginchy
Groovy
Gnarly
Gone
Smokin'
Stacked
Wicked
Twitchin'
Unreal
Fab
Far out
Boss
Glasspacked

-- complimented
cool
ginchy
groovy
gnarly
gone
smokin'
stacked
twitchin'
unreal
fab
far out
boss
glasspacked

-- dude
dude
man
daddy-o
cat
cool head
fox
hunk
stud

-- Dude
Dude
Man
Mamma
Daddy-o
Cat
Cool head
Fox
Hunk
Stud
Chick

-- ,,:
,
,
:

