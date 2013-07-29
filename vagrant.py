from fabric.api import task, sudo, env

@task
def vagrant(name=''):
    """
    optional command `fab vagrant <something>`
    sets the public key for root and then switches to the root user
    """
    from fabtools import vagrant as _vagrant
    _vagrant.vagrant(name)
    sudo('rsync -az /home/vagrant/.ssh/ /root/.ssh/')
    sudo('chown -R root: /root/.ssh')
    env['host_string'] = env['host_string'].replace('vagrant', 'root')
