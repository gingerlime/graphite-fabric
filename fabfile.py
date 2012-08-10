#!/usr/bin/env python
"""

fabric-graphite is a fabric script to install Graphite, Nginx, uwsgi and all dependencies on a debian-based host.

Plus, for a limited time, statsd support!

To execute:

    * Make sure you have fabric installed on your local host (e.g. pip install fabric)
    * run `fab graphite_install -H root@{hostname}` 
      (hostname should be the name of a virtual server you're installing onto)

It might prompt you for the root password on the host you are trying to instal onto.

Best to execute this on a clean virtual machine running Debian 6 (Squeeze). 
Also tested successfully on Ubuntu 12.04 VPS.

"""

from fabric.api import cd, sudo, run, put, settings

def _check_sudo():
    with settings(warn_only=True):
        result = sudo('pwd')
        if result.failed:
            print "Trying to install sudo. Must be root"
            run('apt-get update && apt-get install -y sudo')  

def graphite_install():
    """
    Installs Graphite and dependencies
    """
    _check_sudo()
    sudo('apt-get update && apt-get upgrade -y')
    sudo('apt-get install -y python-dev python-setuptools libxml2-dev libpng12-dev pkg-config build-essential supervisor')
    sudo('easy_install pip')
    sudo('pip install simplejson') # required for django admin
    sudo('pip install carbon')
    sudo('pip install whisper')
    sudo('pip install django==1.3')
    sudo('pip install django-tagging')
    sudo('pip install graphite-web')

    # creating a folder for downloaded source files
    sudo('mkdir -p /usr/local/src')
     
    # Downloading PCRE source (Required for nginx)
    with cd('/usr/local/src'):
        sudo('wget ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-8.30.tar.gz')
        sudo('tar -zxvf pcre-8.30.tar.gz')

    # creating nginx etc and log folders
    sudo('mkdir -p /etc/nginx')
    sudo('mkdir -p /var/log/nginx')
    sudo('chown -R www-data: /var/log/nginx')

    # creating automatic startup scripts for nginx and carbon
    put('config/nginx', '/etc/init.d/', use_sudo=True)
    put('config/carbon', '/etc/init.d/', use_sudo=True)
    sudo('chmod ugo+x /etc/init.d/nginx')
    sudo('chmod ugo+x /etc/init.d/carbon')
    sudo('cd /etc/init.d && update-rc.d nginx defaults')
    sudo('cd /etc/init.d && update-rc.d carbon defaults')

    # installing uwsgi from source
    with cd('/usr/local/src'):
        sudo('wget http://projects.unbit.it/downloads/uwsgi-1.2.3.tar.gz')
        sudo('tar -zxvf uwsgi-1.2.3.tar.gz')
    with cd('/usr/local/src/uwsgi-1.2.3'):
        sudo('make')

        sudo('cp uwsgi /usr/local/bin/')
        sudo('cp nginx/uwsgi_params /etc/nginx/')

    # downloading nginx source
    with cd('/usr/local/src'):
        sudo('wget http://nginx.org/download/nginx-1.2.2.tar.gz')
        sudo('tar -zxvf nginx-1.2.2.tar.gz')

    # installing nginx
    with cd('/usr/local/src/nginx-1.2.2'):
        sudo('./configure --prefix=/usr/local --with-pcre=/usr/local/src/pcre-8.30/ --with-http_ssl_module --with-http_gzip_static_module --conf-path=/etc/nginx/nginx.conf --pid-path=/var/run/nginx.pid --lock-path=/var/lock/nginx.lock --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --user=www-data --group=www-data')
        sudo('make && make install')

    # copying nginx and uwsgi configuration files
    put('config/nginx.conf', '/etc/nginx/', use_sudo=True)
    put('config/uwsgi.conf', '/etc/supervisor/conf.d/', use_sudo=True)

    # installing pixman
    with cd('/usr/local/src'):
        sudo('wget http://cairographics.org/releases/pixman-0.24.4.tar.gz')
        sudo('tar -zxvf pixman-0.24.4.tar.gz')
    with cd('/usr/local/src/pixman-0.24.4'):
        sudo('./configure && make && make install')
    # installing cairo
    with cd('/usr/local/src'):
        sudo('wget http://cairographics.org/releases/cairo-1.12.2.tar.xz')
        sudo('tar -Jxf cairo-1.12.2.tar.xz')
    with cd('/usr/local/src/cairo-1.12.2'):
        sudo('./configure && make && make install')
    # installing py2cairo (python 2.x cairo)
    with cd('/usr/local/src'):
        sudo('wget http://cairographics.org/releases/py2cairo-1.8.10.tar.gz')
        sudo('tar -zxvf py2cairo-1.8.10.tar.gz')
    with cd('/usr/local/src/pycairo-1.8.10'):
        sudo('./configure --prefix=/usr && make && make install')
        sudo('echo "/usr/local/lib" > /etc/ld.so.conf.d/pycairo.conf')
        sudo('ldconfig')
    # setting the carbon config files (default)
    with cd('/opt/graphite/conf/'):
        sudo('cp carbon.conf.example carbon.conf')
        sudo('cp storage-schemas.conf.example storage-schemas.conf')
    # setting carbon pid folder and permissions
    sudo('mkdir -p /var/run/carbon')
    sudo('chown -R www-data: /var/run/carbon')
    # clearing old carbon log files
    put('config/carbon-logrotate', '/etc/cron.daily/', use_sudo=True)

    # starting uwsgi
    sudo('supervisorctl update && supervisorctl start uwsgi')

    # starting carbon-cache
    sudo('/etc/init.d/carbon start')

    # initializing graphite django db
    with cd('/opt/graphite/webapp/graphite'):
        sudo("python manage.py syncdb")

    # changing ownership on graphite folders
    sudo('chown -R www-data: /opt/graphite/')

    # starting nginx
    sudo('nginx')


def statsd_install():
    _check_sudo()
    sudo('add-apt-repository ppa:chris-lea/node.js -y')
    sudo('apt-get update && apt-get upgrade -y')
    sudo('apt-get install git nodejs npm -y')

    with cd('/opt'):
        sudo('git clone https://github.com/etsy/statsd.git')

    with cd('/opt/statsd'):
        sudo('git checkout v0.5.0') # or comment this out and stay on trunk
        put('config/localConfig.js', 'localConfig.js', use_sudo=True)
        sudo('npm install')

    put('config/statsd.conf', '/etc/supervisor/conf.d/', use_sudo=True)

    sudo('supervisorctl update && supervisorctl start statsd')
