# -*- coding: utf-8 -*-

import logging
import multiprocessing.dummy
import multiprocessing
import re
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)

'''
multi is the module to call subprocess in minion host

Ping is a simple test to check if point to point nodes are connected

CLI Example:
.. code-block:: bash
    sudo salt 'node' multi.ping_cmd <hostname>|<ip>
    sudo salt 'node' multi.ping <hostname>|<ip> <hostname>|<ip>....
'''

def _all(func, hosts):
    '''
    Internal function that allow function to perform in all hosts
    '''
    all_instances = []
    # threads should likely scale with cores or interfaces
    cpus = multiprocessing.cpu_count()
    threads = 4 * cpus
    log.debug('multi._all cpus count={},  thread count={}'.format(cpus, threads))
    pool = multiprocessing.dummy.Pool(threads)
    for instance in pool.map(func, hosts):
        all_instances.append(instance)
    
    return all_instances


def _summarize(results):
    '''
    Scan the results and summarize
    '''
    success = []
    failed = []
    errored = []
    slow = []
    avg = []
    for result in results:
        host, rc, out, err = result
        if rc == 0:
            success.append(host)
            rtt = re.match(r'.*rtt min/avg/max/mdev = \d+\.?\d+/(\d+\.?\d+)/', out, re.DOTALL)
            if rtt:
               avg.append({'avg':float(rtt.group(1)), 'host':host})
        if rc == 1:
            failed.append(host)
        if rc == 2:
            errored.append(host)

    log.debug('multi._summarize average={}'.format(avg))

    if avg:
        avg_sum = sum(i.get('avg') for i in avg) / len(avg)
        if len(avg) > 2:
            for i in avg:
                if (avg_sum * len(avg) / 2) < i.get('avg') :
                    log.debug('_summarize: slow host running = {} avg = {}, s'.format( i.get('avg'), avg_sum ))
                    slow.append(i.get('host'))
    else:
        avg_sum = 0 
    
    msg = {}
    msg['succeeded'] = len(success)
    if failed:
        msg['failed'] = " ".join(failed)
    if errored:
        msg['errored'] = " ".join(errored)
    if slow:
        msg['slow'] = " ".join(slow)
    msg['avg'] = avg_sum
    return msg

def iperf_client_cmd( server, cpu=1, port=5201 ):
    '''
    Use iperf to test minion to server
        
    CLI Example:
    .. code-block:: bash
    salt 'node' ceph_sles.iperf server cpu_number=1 port=5201
    '''
    if not server:
        return False
    iperf_cmd = [ "/usr/bin/iperf3", "-fM", "-A"+str(cpu), "-t10", "-c"+server, "-p"+str(port)]
    log.debug('iperf_client_cmd: cmd {}'.format(iperf_cmd))
    proc = Popen(iperf_cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return server, proc.returncode, proc.stdout.read(), proc.stderr.read()

def iperf_server_cmd( cpu=1, port=5201 ):
    '''
    Use iperf to test minion to server
        
    CLI Example:
    .. code-block:: bash
    salt 'node' ceph_sles.iperf server cpu_number=1 port=5201
    '''
    iperf_cmd = [ "/usr/bin/iperf3", "-s", "-D", "-A"+str(cpu),  "-p"+str(port)]
    log.debug('iperf_server_cmd: cmd {}'.format(iperf_cmd))
    with open( "/var/log/iperf_cpu" + str(cpu) + "_port" + str(port) + ".log", "wb") as out, \
    open( "/var/log/iperf_cpu" + str(cpu) + "_port" + str(port) + ".err", "wb" ) as err:
        proc = Popen(iperf_cmd, stdout=out, stderr=err)
    return True


def ping(*hosts):
    '''
    Ping a list of hosts and summarize the results

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.ping <hostname>|<ip> <hostname>|<ip>....
    '''
    # I should be filter all the localhost here? 
    log.debug('ping hostlist={}'.format(list(hosts)))
    results = _all(ping_cmd, list(hosts))
    return _summarize(results)

def ping_cmd(host):
    '''
    Ping a host with 1 packet and return the result

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.ping_cmd <hostname>|<ip>
    '''
    cmd = [ "/usr/bin/ping", "-c1", "-q", "-W1", host ]
    log.debug('ping_cmd hostname={}'.format(host))

    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return host, proc.returncode, proc.stdout.read(), proc.stderr.read()

