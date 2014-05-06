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
from vagrant import vagrant
from fabric.api import cd, sudo, run, put, settings, task


def _check_sudo():
    with settings(warn_only=True):
        result = sudo('pwd')
        if result.failed:
            print "Trying to install sudo. Must be root"
            run('apt-get update && apt-get install -y sudo')


def conf_file(filepath):
    import pkg_resources
    return pkg_resources.resource_filename(__name__,
                                           "/config/{0}".format(filepath))


@task
def graphite_install():
    """
    Installs Graphite and dependencies
    """
    _check_sudo()
    sudo('apt-get update && apt-get upgrade -y')
    sudo('apt-get install -y python-dev python-setuptools libxml2-dev libpng12-dev pkg-config build-essential supervisor make python g++ git-core')
    sudo('easy_install pip')
    sudo('pip install simplejson') # required for django admin
    sudo('pip install git+https://github.com/graphite-project/carbon.git@0.9.x#egg=carbon')
    sudo('pip install git+https://github.com/graphite-project/whisper.git@master#egg=whisper')
    sudo('pip install django==1.5.2')
    sudo('pip install django-tagging')
    sudo('pip install git+https://github.com/graphite-project/graphite-web.git@0.9.x#egg=graphite-web')

    # creating a folder for downloaded source files
    sudo('mkdir -p /usr/local/src')

    # Downloading PCRE source (Required for nginx)
    with cd('/usr/local/src'):
        sudo('wget http://sourceforge.net/projects/pcre/files/pcre/8.33/pcre-8.33.tar.gz/download# -O pcre-8.33.tar.gz')
        sudo('tar -zxvf pcre-8.33.tar.gz')

    # creating nginx etc and log folders
    sudo('mkdir -p /etc/nginx')
    sudo('mkdir -p /var/log/nginx')
    sudo('chown -R www-data: /var/log/nginx')

    # creating automatic startup scripts for nginx and carbon
    put(conf_file('nginx'), '/etc/init.d/', use_sudo=True)
    put(conf_file('carbon'), '/etc/init.d/', use_sudo=True)
    sudo('chmod ugo+x /etc/init.d/nginx')
    sudo('chmod ugo+x /etc/init.d/carbon')
    sudo('cd /etc/init.d && update-rc.d nginx defaults')
    sudo('cd /etc/init.d && update-rc.d carbon defaults')

    # installing uwsgi from source
    with cd('/usr/local/src'):
        sudo('wget http://projects.unbit.it/downloads/uwsgi-1.4.3.tar.gz')
        sudo('tar -zxvf uwsgi-1.4.3.tar.gz')
    with cd('/usr/local/src/uwsgi-1.4.3'):
        sudo('make')

        sudo('cp uwsgi /usr/local/bin/')
        sudo('cp nginx/uwsgi_params /etc/nginx/')

    # downloading nginx source
    with cd('/usr/local/src'):
        sudo('wget http://nginx.org/download/nginx-1.2.7.tar.gz')
        sudo('tar -zxvf nginx-1.2.7.tar.gz')

    # installing nginx
    with cd('/usr/local/src/nginx-1.2.7'):
        sudo('./configure --prefix=/usr/local --with-pcre=/usr/local/src/pcre-8.33/ --with-http_ssl_module --with-http_gzip_static_module --conf-path=/etc/nginx/nginx.conf --pid-path=/var/run/nginx.pid --lock-path=/var/lock/nginx.lock --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --user=www-data --group=www-data')
        sudo('make && make install')

    # copying nginx and uwsgi configuration files
    put(conf_file('nginx.conf'), '/etc/nginx/', use_sudo=True)
    put(conf_file('uwsgi.conf'), '/etc/supervisor/conf.d/', use_sudo=True)

    # installing pixman
    with cd('/usr/local/src'):
        sudo('wget http://cairographics.org/releases/pixman-0.28.2.tar.gz')
        sudo('tar -zxvf pixman-0.28.2.tar.gz')
    with cd('/usr/local/src/pixman-0.28.2'):
        sudo('./configure && make && make install')
    # installing cairo
    with cd('/usr/local/src'):
        sudo('wget http://cairographics.org/releases/cairo-1.12.14.tar.xz')
        sudo('tar -Jxf cairo-1.12.14.tar.xz')
    with cd('/usr/local/src/cairo-1.12.14'):
        sudo('./configure && make && make install')
    # installing py2cairo (python 2.x cairo)
    with cd('/usr/local/src'):
        sudo('wget http://cairographics.org/releases/py2cairo-1.8.10.tar.gz')
        sudo('tar -zxvf py2cairo-1.8.10.tar.gz')
    with cd('/usr/local/src/pycairo-1.8.10'):
        sudo('./configure --prefix=/usr && make && make install')
        sudo('echo "/usr/local/lib" > /etc/ld.so.conf.d/pycairo.conf')
        sudo('ldconfig')
    # installing giraffe dashboard
    with cd('/opt/graphite/webapp'):
        sudo('git clone https://github.com/kenhub/giraffe.git')
    # setting the carbon config files (default)
    with cd('/opt/graphite/conf/'):
        sudo('cp carbon.conf.example carbon.conf')
        sudo('cp storage-schemas.conf.example storage-schemas.conf')
    # clearing old carbon log files
    put(conf_file('carbon-logrotate'), '/etc/cron.daily/', use_sudo=True, mode=0755)

    # initializing graphite django db
    with cd('/opt/graphite/webapp/graphite'):
        sudo("python manage.py syncdb")

    # changing ownership on graphite folders
    sudo('chown -R www-data: /opt/graphite/')

    # starting uwsgi
    sudo('supervisorctl update && supervisorctl start uwsgi')

    # starting carbon-cache
    sudo('/etc/init.d/carbon start')

    # starting nginx
    sudo('nginx')


@task
def statsd_install():
    """
    Installs etsy's node.js statsd and dependencies
    """
    _check_sudo()
    sudo('apt-get update && apt-get upgrade -y')
    sudo('apt-get install -y build-essential supervisor make git-core')
    with cd('/usr/local/src'):
        sudo('wget -N http://nodejs.org/dist/node-latest.tar.gz')
        sudo('tar -zxvf node-latest.tar.gz')
        sudo('cd `ls -rd node-v*` && make install')

    with cd('/opt'):
        sudo('git clone https://github.com/etsy/statsd.git')

    with cd('/opt/statsd'):
        sudo('git checkout v0.7.1') # or comment this out and stay on trunk
        put(conf_file('localConfig.js'), 'localConfig.js', use_sudo=True)
        sudo('npm install')

    put(conf_file('statsd.conf'), '/etc/supervisor/conf.d/', use_sudo=True)
    sudo('supervisorctl update && supervisorctl start statsd')

    # UDP buffer tuning for statsd
    put(conf_file('10-statsd.conf'), '/etc/sysctl.d/', use_sudo=True)
    sudo('sysctl -p /etc/sysctl.d/10-statsd.conf')
