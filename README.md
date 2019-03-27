# Sopel Commands Query

Sopel Commands Query responds to ? to display commands matching patterns

# This code is bad, and the author doesn't feel bad
use at your own risk

# Installation
````
git clone https://github.com/deathbybandaid/sopel-commands-query.git
cd sopel-commands-query
pip3 install .
````

# Usage

## Find commands that start with a letter, or multiple letters

````
<usernick> ?t
<Sopel> The following commands match t: temp, title, t, time, tld, and tell.
````

## Find Command Aliases

````
<usernick>  ?time+
<Sopel>  The following commands match time: t and time.
````

## Find Possible matches based on similarity

````
<deathbybandaid>  ?time?
<Sopel>  The following commands may match time: time, uptime, title, tell, temp, define, t, wt, ip, and in.
````
