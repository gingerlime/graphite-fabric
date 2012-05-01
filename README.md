# Graphite-Fabric - a fabric installer for Graphite

fabric-graphite is a fabric script to install [Graphite](http://graphite.wikidot.com/), Nginx, uwsgi and all dependencies on a debian-based host.

## Why?
I was reading a few [interesting](http://codeascraft.etsy.com/2011/02/15/measure-anything-measure-everything/) [posts](http://obfuscurity.com/Tags/Graphite) about graphite. When I tried to install it however, I couldn't find anything that really covered all the steps. Some covered it well for Apache, others covered Nginx, but had steps missing or assumed the reader knows about them etc.

I'm a big fan of fabric, and try to do all deployments and installations using it. This way I can re-run the process,
and also better document what needs to be done. So instead of writing another guide, I created this fabric script.

## Requirements

 * Workstation running python (version 2.7 recommended). All platforms should be supported.
 * [Fabric](http://docs.fabfile.org/en/1.4.1/index.html) - can be installed via `pip install fabric` or `easy_install fabric`
 * a new VPS/Dedicated server running a Debian-based distribution (Debian, Ubuntu etc)

### Target Host

Best to execute this on a clean virtual machine running Debian 6 (Squeeze).
Also tested successfully on Ubuntu 12.04 VPS.

## Installation Instructions 

run `fab graphite_install -H root@{hostname}` 
(hostname should be the name of a virtual server you're installing onto)

It might prompt you for the root password on the host you are trying to instal onto.

You can use it with a user other than root, as long as this user can `sudo`.

During the installation, you would be asked to set up the django superuser account. You might want to create an account,
but it's not strictly necessary. If you answer `no`, the installation will still work fine.

## After Installation

Simply open your browser and go to `http://[your-hostname]/graphite/` ! It should be up and running.

Of course there's a lot more configuration to be done, but at the very least you should have a working environment to
play with Graphite.

## Thanks

Thanks to the authors of these online guides and resources who provided very useful information that I stitched together into this
fabric script, and others who provided inspiration about Graphite in General:

 * [Graphite Docs](http://readthedocs.org/docs/graphite/en/latest/install.html)
 * [frl1nuX - Graphite and Nginx](http://www.frlinux.eu/?p=199)
 * [Agile Testing - Installing and configuring Graphite](http://agiletesting.blogspot.de/2011/04/installing-and-configuring-graphite.html)
 * [Corey Goldberg - Installing Graphite 0.9.9 on Ubuntu 12.04 LTS](http://coreygoldberg.blogspot.de/2012/04/installing-graphite-099-on-ubuntu-1204.html)

Although not installed with this fabric script, I'd love to try these some time:
 * [Graphene](http://jondot.github.com/graphene/)
 * [GDash](https://github.com/ripienaar/gdash)
 * [Logster](https://github.com/etsy/logster)

## DISCLAIMER

Please try this at your own risk. Please run this only with a newly installed host that you can easily throw away!
I tested it with both Debian 6 and Ubuntu 12.04 successfully. However, you may experience different results.

## Help and Contribution

I'd be happy to try to help if I can, but given the complexity of linux-based operating-systems, and my limited time, I might not be able to
know why a certain operation fails or an error is generated. Feel free to fork for your own special requirements or needs.
