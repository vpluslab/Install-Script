#!/usr/bin/python3

import os
import subprocess
import sys
import getopt
from subprocess import Popen, PIPE, STDOUT
import socket
import shutil

def get_ubuntu_version():
    ubuntu_version = subprocess.check_output(['lsb_release', '-r'])
    if ubuntu_version.decode('utf-8').find('18.04') > 0 :
        return "18.04"
    elif ubuntu_version.decode('utf-8').find('20.04') > 0 :
        return "20.04"
    elif ubuntu_version.decode('utf-8').find('22.04') > 0 :
        return "22.04"
    else:
        return "This system is not supported"


def check_net_tools():
    apt_package = subprocess.Popen('apt list --installed', stdin = PIPE, stdout = PIPE, stderr = STDOUT, shell = True)
    net_tools_package = subprocess.Popen('grep net-tools', stdin = apt_package.stdout, stdout = PIPE, stderr = STDOUT, shell = True)
    outs = net_tools_package.communicate()[0]
    #print(outs.decode())
    if outs.decode().startswith('net-tools/'):
        return True
    return False

def check_postgresql():
    try:
        postgre_version = subprocess.check_output(['psql', '-V'])
        return True
    except FileNotFoundError:
        return False

def check_redis():
    try:
        redis_version = subprocess.check_output(['redis-server', '--version'])
        return True
    except FileNotFoundError:
        return False

def check_compile_environment():
    if not os.path.isfile('crown_tset.c'):
        with open ('crown_test.c' ,'w') as code:
            code.write('#include <stdio.h>\n')
            code.write('\n')
            code.write('int main()\n')
            code.write('{\n')
            code.write('\tprintf(\"crown environment test\");\n')
            code.write('\treturn 0;\n')
            code.write('}\n')
    if os.path.isfile('crown_test.c'):
        result = os.system('gcc crown_test.c -o crown_test')
    else:
        sys.exit('CROWN2: [error] Fail to check compile env. because test file does not eixst')
    if os.path.isfile('crown_test'):
        output = subprocess.check_output(['./crown_test'])
        if output.decode('utf-8') == 'crown environment test':
            print('CROWN2: [info] Compile packages are already installed')
            return True
        else:
            sys.exit('CROWN2: [error] Wrong test data.')
    else:
        print('CROWN2: [info] Compile packages are not found')
        return False

def check_port(port_num):
    port = subprocess.Popen('netstat -an', stdin=PIPE, stdout=PIPE ,stderr=STDOUT, shell=True)
    define_port = subprocess.Popen('grep :\'' + port_num + ' \'', stdin=port.stdout, stdout=PIPE, stderr=STDOUT, shell= True)
    outs = define_port.communicate()[0]
    return outs

def rewrite_cilly(file_location):
    if not os.path.exists(file_location):
        sys.stderr.write('CROWN2: [error] cilly is not exist. plz check install location')
        return
    cilly_location = file_location[:-9]
    orig_file = open(file_location, 'r')
    cilly_buffer = orig_file.read()
    orig_file.close()

    new_file = open(file_location, 'w')
    
    for line in cilly_buffer.split('\n'):
        if line.startswith('$ENV{'):
            new_file.write('$ENV{\'OCAMLFIND_CONF\'}=\'' + cilly_location + 'lib/findlib.conf\';\n')
        else:
            new_file.write(line + '\n')
    new_file.close()

def rewrite_findlib_conf(file_location):
    findlib_location = file_location[:-13]
    if not os.path.exists(file_location):
        sys.stderr.write('CROWN2: [error] findlib.conf is not exist. plz check install location')
        return
    orig_file = open(file_location, 'r')
    findlib_buffer = orig_file.read()
    orig_file.close()

    new_file = open(file_location, 'w')

    for line in findlib_buffer.split('\n'):
        if line.startswith('destdir='):
            new_file.write('destdir="' + findlib_location + '"\n')
        elif line.startswith('path='):
            new_file.write('path="' + findlib_location + '"\n')
        else:
            new_file.write(line + '\n')
    new_file.close()

def rewrite_backend_config(backend_location, backend_port):
    config_file_name = backend_location + os.sep + 'CR2Server' + os.sep + 'config.dat'
    with open(config_file_name, 'w') as config_file:
        config_file.write('working="' + backend_location + os.sep + 'working"\n')
        config_file.write('bin="' + backend_location + os.sep + 'bin"\n')
        config_file.write('host="' + get_ip_address() + '"\n')
        config_file.write('port=' + backend_port + '\n')


def get_ip_address():
    return socket.gethostbyname(socket.gethostname())

def rewrite_webserver_conf(file_location, backend_port, webserver_port, webserver_ws_port):
    if not os.path.exists(file_location):
        sys.stderr.write('CROWN2: [error] CROWN_webserver/package.json is not exist. plz check install location')
        sys.exit(2)
    
    orig_file = open(file_location, 'r')
    package_buffer = orig_file.read()
    orig_file.close()

    new_file = open(file_location, 'w')

    for line in package_buffer.split('\n'):
        if line.startswith('    "start:dev":'):
            new_file.write('    "start:dev": "NODE_ENV=dev BACKEND_API_END_POINT=http://' + get_ip_address() +':'+backend_port+'/v1/api BACKEND_WS_END_POINT=ws://' + get_ip_address() + ':' + backend_port + '/ws THIS_HTTP_PORT=' + webserver_port + ' THIS_WS_PORT=' + webserver_ws_port + ' PREFIX_REDIS_NAME=CROWN2 nest start --watch",\n')
        else:
            new_file.write(line + '\n')
    new_file.close()

def rewrite_frontend_conf(file_location, webserver_port, webserver_ws_port):
    if not os.path.exists(file_location):
        sys.stderr.write('CROWN2: [error] CROWN_frontend/package.json is not exist. plz check install location')
        sys.exit(2)

    orig_file = open(file_location, 'r')
    package_buffer = orig_file.read()
    orig_file.close()

    new_file = open(file_location, 'w')
    for line in package_buffer.split('\n'):
        if line.startswith('    "start-offline": "'):
            new_file.write('    "start-offline": "__SERVER_API_ENDPOINT__=\'http://' + get_ip_address() + ':' + webserver_port + '/v1/api\' __SERVER_WS_ENDPOINT__=\'ws://' + get_ip_address() + ':' + webserver_ws_port + '/ws\' npm run start",\n')
        else:
            new_file.write(line + '\n')
    new_file.close()

def rewrite_frontend_port(file_location, front_port):
    if not os.path.exists(file_location):
        sys.stderr.write('CROWN2: [error] CROWN_frontend/webpack.config.dev.js is not exist. plz check install location')
        sys.exit(2)
        
    orig_file = open(file_location, 'r')
    web_port_buffer = orig_file.read()
    orig_file.close()

    with open(file_location, 'w') as new_file:
        for line in web_port_buffer.split('\n'):
            if line.startswith('    port:'):
                new_file.write('    port: ' + front_port + ',\n');
            else:
                new_file.write(line + '\n')

def register_service(location):
    with open('/etc/systemd/system/crown_backend.service','w') as f:
        f.write('[Unit]\n')
        f.write('Description=CROWN2 Backend\n')
        f.write('\n')
        f.write('[Service]\n')
        f.write('WorkingDirectory=' + location + os.sep + 'CROWN_backend' + os.sep + 'CR2Server\n')
        f.write('ExecStart=' + location + os.sep + 'CROWN_backend' + os.sep + 'CR2Server' + os.sep + 'main.py\n')
        f.write('Restart=on-failure\n')
        f.write('RestartPreventExitStatus=255\n')
        f.write('\n')
        f.write('[Install]\n')
        f.write('WantedBy=multi-user.target\n')

    with open('/etc/systemd/system/crown_webserver.service','w') as f:
        f.write('[Unit]\n')
        f.write('Description=CROWN2 Webserver\n')
        f.write('\n')
        f.write('[Service]\n')
        f.write('WorkingDirectory=' + location + os.sep + 'CROWN_webserver\n')
        f.write('ExecStart=/usr/local/bin/npm run start:dev\n')
        f.write('Restart=on-failure\n')
        f.write('RestartPreventExitStatus=255\n')
        f.write('\n')
        f.write('[Install]\n')
        f.write('WantedBy=multi-user.target\n')

    with open('/etc/systemd/system/crown_frontend.service','w') as f:
        f.write('[Unit]\n')
        f.write('Description=CROWN2 Frontend\n')
        f.write('\n')
        f.write('[Service]\n')
        f.write('WorkingDirectory=' + location + os.sep + 'CROWN_frontend\n')
        f.write('ExecStart=/usr/local/bin/npm run start-offline\n')
        f.write('Restart=on-failure\n')
        f.write('RestartPreventExitStatus=255\n')
        f.write('\n')
        f.write('[Install]\n')
        f.write('WantedBy=multi-user.target\n')

    subprocess.run('systemctl daemon-reload', shell = True)
    subprocess.run('systemctl enable crown_backend', shell = True)
    subprocess.run('systemctl enable crown_webserver', shell = True)
    subprocess.run('systemctl enable crown_frontend', shell = True)
    subprocess.run('systemctl start crown_backend', shell = True)
    subprocess.run('systemctl start crown_webserver', shell = True)
    subprocess.run('systemctl start crown_frontend', shell = True)

def main(argv):
    #1 stop service if exists
    os.system('service crown2_backend stop')
    os.system('service crown2_webserver stop')
    os.system('service crown2_frontend stop')

    #2 get ubuntu version
    ubuntu_version = get_ubuntu_version()
    if ubuntu_version == 'This system is not supproted':
        sys.exit('CROWN2 supprots ubuntu version 18.04, 20.04 and 22.04')
        os.system('service crown2_backend start')
        os.system('service crown2_webserver start')
        os.system('service crown2_frontend start')
    else:
        print('CROWN2: [info] Current version: {}'.format(ubuntu_version))

    install_path = os.getcwd()
    backend_port = '20000'
    webserver_port = '20010'
    webserver_websocket = '20011'
    frontend_port = '80'

    try:
        opts, other_args = getopt.getopt(argv[1:], "i:p:", ["inst=","port="])
    except getopt.GetoptError:
        print(argv[0], '-i <install_path> -p <port_num> ')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-i', '--inst'):
            install_path = arg
        elif opt in ('-p', '--port'):
            frontend_port = arg


    #check net-tools is installed.
    if check_net_tools() == True:
        print('CROWN2: [info] Skip installing net-tools package')
    else:
        print('CROWN2: [info] Install net-tools package')
        if ubuntu_version == '18.04':
            os.system('dpkg -i net-tools_18/net-tools_1.60+git20161116.90da8a0-1ubuntu1_amd64.deb')
        elif ubuntu_version == '20.04':
            os.system('dpkg -i net-tools_20/net-tools_1.60+git20180626.aebd88e-1ubuntu1_amd64.deb')
        elif ubuntu_version == '22.04':
            pass

    gcc_installed = check_compile_environment()

    if not os.path.isdir(install_path):
        os.makedirs(install_path)
    
    #Setting up install path
    while os.path.isdir(install_path + os.sep + 'CROWN2'):
        update_input = input('CROWN2 is already installed in ' + install_path + '. If you insert \'y\' or \'Y\', CROWN2 will be updated: ')
        if update_input == 'y':
            break
        install_path = input('Insert new CROWN2 path: ')
        if not os.path.isdir(install_path):
            os.makedirs(install_path)
    
    #Setting up front end port

    while check_port(frontend_port).decode() != '':
        print(check_port(frontend_port).decode())
        print('Port number ' + frontend_port + ' is already used.\n')
        frontend_port = input('Insert port number: ')

    #Setting up backend port. If port is already used, backend prot will be increased.
    while check_port(backend_port).decode() != '' and backend_port != frontend_port:
        int_backend_port = int(backend_port)
        int_backend_port = int_backend_port + 1
        backend_port = str(int_backend_port)

    while check_port(webserver_port).decode() != '' and webserver_port != frontend_port and webserver_port != backend_port:
        int_webserver_port =int(webserver_port)
        int_webserver_port = int_webserver_port + 1
        webserver_port = str(int_webserver_port)

    while check_port(webserver_websocket).decode() != '' and webserver_websocket != frontend_port and webserver_websocket != backend_port and webserver_websocket!= webserver_port:
        int_webserver_websocket =int(webserver_websocket)
        int_webserver_websocket = int_webserver_websocket + 1
        webserver_websocket = str(int_webserver_websocket)

    print('------------------------------------------------------------------')
    print('   Install Path      : ' + install_path)
    print('   Service Port      : ' + frontend_port)
    print(' below will be removed.')
    print(' Backend Port        : ' + backend_port)
    print(' Webserver Port      : ' + webserver_port)
    print(' Webserver websocket : ' + webserver_websocket)
    print('------------------------------------------------------------------')

    #2 extract file to CROWN2_tmp
    print('CROWN2: [info] Installing packages')
    if not os.path.isdir(install_path + os.sep + 'CROWN2_tmp'):
        os.makedirs(install_path + os.sep + 'CROWN2_tmp')

    if os.path.exists('CROWN2.tar.gz'):
        shutil.copy('CROWN2.tar.gz', install_path + os.sep + 'CROWN2_tmp')
    else:
        print('Error: CROWN2 install package is not exist\n')
        sys.exit(2)
    os.chdir(install_path + os.sep + 'CROWN2_tmp')
    subprocess.run('tar xvf CROWN2.tar.gz', shell=True)

    os.chdir(os.getcwd() + os.sep + 'CROWN_install_packages')

    #3 copy node to CROWN2 directory
    subprocess.run('tar xvf node-v16.17.0-linux-x64.tar.gz', shell=True)
    shutil.move('node-v16.17.0-linux-x64', install_path + os.sep + 'CROWN2/node-v16.17.0-linux-x64')
    subprocess.run('ln -s ' + install_path + os.sep + 'CROWN2' + os.sep + 'node-v16.17.0-linux-x64' + os.sep + 'bin' + os.sep + 'node /usr/local/bin/node', shell=True )
    subprocess.run('ln -s ' + install_path + os.sep + 'CROWN2' + os.sep + 'node-v16.17.0-linux-x64' + os.sep + 'bin' + os.sep + 'npm /usr/local/bin/npm', shell=True )
    subprocess.run('ln -s ' + install_path + os.sep + 'CROWN2' + os.sep + 'node-v16.17.0-linux-x64' + os.sep + 'bin' + os.sep + 'npx /usr/local/bin/npx', shell=True )

    #4 copy CROWN_backend to CROWN2 directory
    subprocess.run('tar xvf CROWN_backend.tar', shell=True)
    shutil.move('CROWN_backend', install_path + os.sep + 'CROWN2')
    
    if not os.path.isfile('/usr/lib/x86_64-linux-gnu/libclang.so'):
        shutil.move('libclang.so', '/usr/lib/x86_64-linux-gnu/libclang.so')

    #5 copy CROWN_webserver to CROWN2 directory
    subprocess.run('tar xvf CROWN_webserver.tar', shell=True)
    shutil.move('CROWN_webserver', install_path + os.sep + 'CROWN2')

    rewrite_webserver_conf(install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_webserver' + os.sep + 'package.json' , backend_port, webserver_port, webserver_websocket)

    #6 copy CROWN_frontend to CROWN2 directory
    subprocess.run('tar xvf CROWN_frontend.tar', shell=True)
    shutil.move('CROWN_frontend', install_path + os.sep + 'CROWN2')

    rewrite_frontend_conf( install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_frontend' + os.sep + 'package.json', webserver_port, webserver_websocket) 
    rewrite_frontend_port( install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_frontend' + os.sep + 'webpack.config.dev.js' , frontend_port)

    #7 edit cilly
    rewrite_cilly(install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_backend' + os.sep + 'CROWN_tc_generator' + os.sep + 'cil' + os.sep+ 'bin' + os.sep + 'cilly')

    rewrite_findlib_conf(install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_backend' + os.sep + 'CROWN_tc_generator' + os.sep + 'cil' + os.sep + 'lib' + os.sep + 'findlib.conf')

    rewrite_backend_config(install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_backend', backend_port)

    #make working directory
    if not os.path.exists(install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_backend' + os.sep + 'working'):
        os.makedirs(install_path + os.sep + 'CROWN2' + os.sep + 'CROWN_backend' + os.sep + 'working')
# 1. directory setting
# default: current directory + CROWN2/ ....

    print('CROWN2: [info] Install gcc packages ' + ubuntu_version)
    if gcc_installed == False:
        if ubuntu_version == '18.04':
            subprocess.run('dpkg -i gcc_packages_18_04/*.deb', shell = True)
        elif ubuntu_version == '20.04':
            subprocess.run('dpkg -i gcc_packages_20_04/*.deb', shell = True)
        elif ubuntu_version == '22.04':
            pass
    if not os.path.isfile('/usr/bin/unzip'):
        print('CROWN2: [info] copy unzip to /usr/bin/')
        shutil.move('bin/unzip','usr/bin/unzip')
    if not os.path.isfile('/usr/bin/zip'):
        print('CROWN2: [info] copy zip to /usr/bin/')
        shutil.move('bin/zip','usr/bin/zip')

    if ubuntu_version == '18.04':
        if not os.path.isfile('/usr/lib/gcc/x86_64-linux-gnu/7/libstdc++.a'):
            shutil.move('./gcc_packages_18_04/libstdc++.a','/usr/lib/gcc/x86_64-linux-gnu/7/libstdc++.a')
    elif ubuntu_version == '20.04':
        if not os.path.isfile('/usr/lib/gcc/x86_64-linux-gnu/9/libstdc++.a'):
            shutil.move('./gcc_packages_20_04/libstdc++.a','/usr/lib/gcc/x86_64-linux-gnu/9/libstdc++.a')
    elif ubuntu_version == '22.04':
        pass

    print('CROWN2: [info] Install gcov packages ' + ubuntu_version)
    if ubuntu_version == '18.04':
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/jinja2') and not os.path.isdir('/usr/lib/python3/dist-packages/jinja2'):
            print( 'CROWN2: [info] copy python library:jinja2')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/jinja2', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/Jinja2-3.0.3.dist-info', '/usr/local/lib/python3.6/dist-packages')
        
        if os.path.isdir('/usr/local/lib/python3.6/dist-packages/gcovr_crown'):
            print( 'CROWN2: [info] remove python library:gcovr_crown')
            shutil.rmtree('/usr/local/lib/python3.6/dist-packages/gcovr_crown')
        print( 'CROWN2: [info] copy python library:gcovr_crown')
        shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/gcovr_crown', '/usr/local/lib/python3.6/dist-packages')
                                                                             
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/markupsafe') and not os.path.isdir('/usr/lib/python3/dist-packages/markupsafe'):
            print( 'CROWN2: [info] remove python library:markupsafe')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/markupsafe', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/MarkupSafe-2.0.1.dist-info', '/usr/local/lib/python3.6/dist-packages')
                                                                                                                 
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/lxml') and not os.path.isdir('/usr/lib/python3/dist-packages/lxml'):
            print( 'CROWN2: [info] remove python library:lxml')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/lxml_18_04', '/usr/local/lib/python3.6/dist-packages/lxml')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/lxml-4.6.4.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/pygments'):
            print( 'CROWN2: [info] remove python library:pygments')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/pygments', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./gcovr_18_04/gcovr/lib/python3/dist-packages/Pygments-2.10.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        shutil.move('./gcovr_18_04/gcovr/bin/gcovr_crown' , '/usr/local/bin/gcovr_crown')
        shutil.move('./gcovr_18_04/gcovr/bin/pygmentize' , '/usr/local/bin/pygmentize')

    
    elif ubuntu_version == '20.04':
        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/jinja2') and not os.path.isdir('/usr/lib/python3/dist-packages/jinja2'):
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/jinja2', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/Jinja2-3.0.3.dist-info', '/usr/local/lib/python3.8/dist-packages')
            
        if os.path.isdir('/usr/local/lib/python3.8/dist-packages/gcovr_crown'):
            shutil.rmtree('/usr/local/lib/python3.8/dist-packages/gcovr_crown')
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/gcovr_crown', '/usr/local/lib/python3.8/dist-packages')
                                                                    
        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/markupsafe') and not os.path.isdir('/usr/lib/python3/dist-packages/markupsafe'):
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/markupsafe', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/MarkupSafe-2.0.1.dist-info', '/usr/local/lib/python3.8/dist-packages')
                                                        
        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/lxml') and not os.path.isdir('/usr/lib/python3/dist-packages/lxml') :
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/lxml_20_04', '/usr/local/lib/python3.8/dist-packages/lxml')
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/lxml-4.6.4.dist-info', '/usr/local/lib/python3.8/dist-packages')
            
        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/pygments'):
                                                           
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/pygments', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./gcovr_20_04/gcovr/lib/python3/dist-packages/Pygments-2.10.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        shutil.move('./gcovr_20_04/gcovr/bin/gcovr_crown' , '/usr/local/bin/gcovr_crown')
        subprocess.call(['chmod', '777', '/usr/local/bin/gcovr_crown'])
        shutil.move('./gcovr_20_04/gcovr/bin/pygmentize' , '/usr/local/bin/pygmentize')
        subprocess.call(['chmod', '777', '/usr/local/bin/pygmentize'])
    elif ubuntu_version == '22.04':
            pass

    print('CROWN2: [info] Install backend server packages ' + ubuntu_version)
    if ubuntu_version == '18.04':
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/anyio') and not os.path.isdir('/usr/lib/python3/dist-packages/anyio'):
            print( 'CROWN2: [info] copy python library:anyio')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/anyio', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/anyio-3.6.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/asgiref') and not os.path.isdir('/usr/lib/python3/dist-packages/asgiref'):
            print( 'CROWN2: [info] copy python library:asgiref')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/asgiref', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/asgiref-3.4.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/clang') and not os.path.isdir('/usr/lib/python3/dist-packages/clang'):
            print( 'CROWN2: [info] copy python library:clang')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/clang', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/clang-14.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/click') and not os.path.isdir('/usr/lib/python3/dist-packages/click'):
            print( 'CROWN2: [info] copy python library:click')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/click', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/click-8.0.4.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/contextlib2') and not os.path.isdir('/usr/lib/python3/dist-packages/contextlib2'):
            print( 'CROWN2: [info] copy python library:contextlib2')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/contextlib2', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/contextlib2-21.6.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/contextvars') and not os.path.isdir('/usr/lib/python3/dist-packages/contextvars'):
            print( 'CROWN2: [info] copy python library:contextvars')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/contextvars', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/contextvars-2.4.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isfile('/usr/local/lib/python3.6/dist-packages/dataclasses.py') and not os.path.isfile('/usr/lib/python3/dist-packages/dataclasses.py'):
            print( 'CROWN2: [info] copy python library:dataclasses')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/dataclasses.py', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/dataclasses-0.8.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/dotenv') and not os.path.isdir('/usr/lib/python3/dist-packages/dotenv'):
            print( 'CROWN2: [info] copy python library:dotenv')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/dotenv', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/python_dotenv-0.20.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/fastapi') and not os.path.isdir('/usr/lib/python3/dist-packages/fastapi'):
            print( 'CROWN2: [info] copy python library:fastapi')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/fastapi', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/fastapi-0.79.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/h11') and not os.path.isdir('/usr/lib/python3/dist-packages/h11'):
            print( 'CROWN2: [info] copy python library:h11')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/h11', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/h11-0.13.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/httptools') and not os.path.isdir('/usr/lib/python3/dist-packages/httptools'):
            print( 'CROWN2: [info] copy python library:httptools')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/httptools', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/httptools-0.3.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/idna') and not os.path.isdir('/usr/lib/python3/dist-packages/idna'):
            print( 'CROWN2: [info] copy python library:idna')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/idna', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/idna-3.3.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/immutables') and not os.path.isdir('/usr/lib/python3/dist-packages/immutables'):
            print( 'CROWN2: [info] copy python library:immutables')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/immutables', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/immutables-0.18.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/importlib_metadata') and not os.path.isdir('/usr/lib/python3/dist-packages/importlib_metadata'):
            print( 'CROWN2: [info] copy python library:importlib_metadata')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/importlib_metadata', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/importlib_metadata-4.8.3.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/multipart') and not os.path.isdir('/usr/lib/python3/dist-packages/multipart'):
            print( 'CROWN2: [info] copy python library:multipart')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/multipart', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/python_multipart-0.0.5.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/psutil') and not os.path.isdir('/usr/lib/python3/dist-packages/ps_util'):
            print( 'CROWN2: [info] copy python library:psutil')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/psutil', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/psutil-5.9.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/pydantic') and not os.path.isdir('/usr/lib/python3/dist-packages/pydantic'):
            print( 'CROWN2: [info] copy python library:pydantic')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/pydantic', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/pydantic-1.9.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/sniffio') and not os.path.isdir('/usr/lib/python3/dist-packages/sniffio'):
            print( 'CROWN2: [info] copy python library:sniffio')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/sniffio', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/sniffio-1.2.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/starlette') and not os.path.isdir('/usr/lib/python3/dist-packages/starlette'):
            print( 'CROWN2: [info] copy python library:starlette')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/starlette', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/starlette-0.19.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isfile('/usr/local/lib/python3.6/dist-packages/typing_extensions.py') and not os.path.isfile('/usr/lib/python3/dist-packages/typing_extensions.py'):
            print( 'CROWN2: [info] copy python library:typing_extensions')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/typing_extensions.py', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/typing_extensions-4.1.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/uvicorn') and not os.path.isdir('/usr/lib/python3/dist-packages/uvicorn'):
            print( 'CROWN2: [info] copy python library:uvicorn')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/uvicorn', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/uvicorn-0.20.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/uvloop') and not os.path.isdir('/usr/lib/python3/dist-packages/uvloop'):
            print( 'CROWN2: [info] copy python library:uvloop')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/uvloop', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/uvloop-0.14.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/watchgod') and not os.path.isdir('/usr/lib/python3/dist-packages/watchgod'):
            print( 'CROWN2: [info] copy python library:watchgod')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/watchgod', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/watchgod-0.7.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/websockets') and not os.path.isdir('/usr/lib/python3/dist-packages/websockets'):
            print( 'CROWN2: [info] copy python library:websockets')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/websockets', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/websockets-9.1.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/yaml') and not os.path.isdir('/usr/lib/python3/dist-packages/watchgod'):
            print( 'CROWN2: [info] copy python library:yaml')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/yaml', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/_yaml', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/PyYAML-6.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isfile('/usr/local/lib/python3.6/dist-packages/zipp.py') and not os.path.isfile('/usr/lib/python3/dist-packages/zipp.py'):
            print( 'CROWN2: [info] copy python library:zipp')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/zipp.py', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_18_04/fastapi/lib/python3/dist-packages/zipp-3.6.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        shutil.move('./fastapi_18_04/fastapi/bin/dotenv' , '/usr/local/bin/dotenv')
        subprocess.call(['chmod', '777', '/usr/local/bin/dotenv'])
        shutil.move('./fastapi_18_04/fastapi/bin/uvicorn' , '/usr/local/bin/uvicorn')
        subprocess.call(['chmod', '777', '/usr/local/bin/uvicorn'])
        shutil.move('./fastapi_18_04/fastapi/bin/watchgod' , '/usr/local/bin/watchgod')
        subprocess.call(['chmod', '777', '/usr/local/bin/watchgod'])

    elif ubuntu_version == '20.04':

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/anyio') and not os.path.isdir('/usr/lib/python3/dist-packages/anyio'):
            print( 'CROWN2: [info] copy python library:anyio')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/anyio', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/anyio-3.6.2.dist-info', '/usr/local/lib/python3.6/dist-packages')

        '''
        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/asgiref') and not os.path.isdir('/usr/lib/python3/dist-packages/asgiref'):
            print( 'CROWN2: [info] copy python library:asgiref')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/asgiref', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/asgiref-3.4.1.dist-info', '/usr/local/lib/python3.6/dist-packages')
        '''

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/clang') and not os.path.isdir('/usr/lib/python3/dist-packages/clang'):
            print( 'CROWN2: [info] copy python library:clang')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/clang', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/clang-14.0.dist-info', '/usr/local/lib/python3.8/dist-packages')
        '''
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/click') and not os.path.isdir('/usr/lib/python3/dist-packages/click'):
            print( 'CROWN2: [info] copy python library:click')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/click', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/click-8.0.4.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/contextlib2') and not os.path.isdir('/usr/lib/python3/dist-packages/contextlib2'):
            print( 'CROWN2: [info] copy python library:contextlib2')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/contextlib2', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/contextlib2-21.6.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/contextvars') and not os.path.isdir('/usr/lib/python3/dist-packages/contextvars'):
            print( 'CROWN2: [info] copy python library:contextvars')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/contextvars', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/contextvars-2.4.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isfile('/usr/local/lib/python3.6/dist-packages/dataclasses.py') and not os.path.isfile('/usr/lib/python3/dist-packages/dataclasses.py'):
            print( 'CROWN2: [info] copy python library:dataclasses')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/dataclasses.py', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/dataclasses-0.8.dist-info', '/usr/local/lib/python3.6/dist-packages')
        '''
        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/dotenv') and not os.path.isdir('/usr/lib/python3/dist-packages/dotenv'):
            print( 'CROWN2: [info] copy python library:dotenv')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/dotenv', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/python_dotenv-0.21.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/fastapi') and not os.path.isdir('/usr/lib/python3/dist-packages/fastapi'):
            print( 'CROWN2: [info] copy python library:fastapi')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/fastapi', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/fastapi-0.88.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/gevent') and not  os.path.isdir('/usr/lib/python3/dist-packages/gevent'):
            print( 'CROWN2: [info] copy python library:gevent')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/gevent', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/gevent-22.10.2.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/greenlet') and not  os.path.isdir('/usr/lib/python3/dist-packages/greenlet'):
            print( 'CROWN2: [info] copy python library:greenlet')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/greenlet', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/greenlet-2.0.1.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/h11') and not os.path.isdir('/usr/lib/python3/dist-packages/h11'):
            print( 'CROWN2: [info] copy python library:h11')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/h11', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/h11-0.14.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/httptools') and not os.path.isdir('/usr/lib/python3/dist-packages/httptools'):
            print( 'CROWN2: [info] copy python library:httptools')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/httptools', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/httptools-0.5.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        '''
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/idna') and not os.path.isdir('/usr/lib/python3/dist-packages/idna'):
            print( 'CROWN2: [info] copy python library:idna')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/idna', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/idna-3.3.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/immutables') and not os.path.isdir('/usr/lib/python3/dist-packages/immutables'):
            print( 'CROWN2: [info] copy python library:immutables')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/immutables', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/immutables-0.18.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/importlib_metadata') and not os.path.isdir('/usr/lib/python3/dist-packages/importlib_metadata'):
            print( 'CROWN2: [info] copy python library:importlib_metadata')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/importlib_metadata', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/importlib_metadata-4.8.3.dist-info', '/usr/local/lib/python3.6/dist-packages')
        '''

        if not os.path.isfile('/usr/local/lib/python3.8/dist-packages/multipart.py') and not os.path.isfile('/usr/lib/python3/dist-packages/multipart.py'):
            print( 'CROWN2: [info] copy python library:multipart')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/multipart.py', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/multipart-0.2.4.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/psutil') and not os.path.isdir('/usr/lib/python3/dist-packages/ps_util'):
            print( 'CROWN2: [info] copy python library:psutil')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/psutil', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/psutil-5.9.4.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/pydantic') and not os.path.isdir('/usr/lib/python3/dist-packages/pydantic'):
            print( 'CROWN2: [info] copy python library:pydantic')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/pydantic', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/pydantic-1.10.2.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/sniffio') and not os.path.isdir('/usr/lib/python3/dist-packages/sniffio'):
            print( 'CROWN2: [info] copy python library:sniffio')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/sniffio', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/sniffio-1.3.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/starlette') and not os.path.isdir('/usr/lib/python3/dist-packages/starlette'):
            print( 'CROWN2: [info] copy python library:starlette')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/starlette', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/starlette-0.22.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isfile('/usr/local/lib/python3.8/dist-packages/typing_extensions.py') and not os.path.isfile('/usr/lib/python3/dist-packages/typing_extensions.py'):
            print( 'CROWN2: [info] copy python library:typing_extensions')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/typing_extensions.py', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/typing_extensions-4.4.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/uvicorn') and not os.path.isdir('/usr/lib/python3/dist-packages/uvicorn'):
            print( 'CROWN2: [info] copy python library:uvicorn')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/uvicorn', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/uvicorn-0.20.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/uvloop') and not os.path.isdir('/usr/lib/python3/dist-packages/uvloop'):
            print( 'CROWN2: [info] copy python library:uvloop')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/uvloop', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/uvloop-0.17.0.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/watchfiles') and not os.path.isdir('/usr/lib/python3/dist-packages/watchfiles'):
            print( 'CROWN2: [info] copy python library:watchfiles')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/watchfiles', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/watchfiles-0.18.1.dist-info', '/usr/local/lib/python3.8/dist-packages')

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/websockets') and not os.path.isdir('/usr/lib/python3/dist-packages/websockets'):
            print( 'CROWN2: [info] copy python library:websockets')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/websockets', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/websockets-10.4.dist-info', '/usr/local/lib/python3.8/dist-packages')

        '''
        if not os.path.isdir('/usr/local/lib/python3.6/dist-packages/yaml') and not os.path.isdir('/usr/lib/python3/dist-packages/watchgod'):
            print( 'CROWN2: [info] copy python library:yaml')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/yaml', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/_yaml', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/PyYAML-6.0.dist-info', '/usr/local/lib/python3.6/dist-packages')

        if not os.path.isfile('/usr/local/lib/python3.6/dist-packages/zipp.py') and not os.path.isfile('/usr/lib/python3/dist-packages/zipp.py'):
            print( 'CROWN2: [info] copy python library:zipp')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zipp.py', '/usr/local/lib/python3.6/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zipp-3.6.0.dist-info', '/usr/local/lib/python3.6/dist-packages')
        '''

        if not os.path.isdir('/usr/local/lib/python3.8/dist-packages/zope') and not os.path.isdir('/usr/lib/python3/dist-packages/zope'):
            print( 'CROWN2: [info] copy python library:zope')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zope', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zope.event-4.5.0.dist-info', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zope.event-4.5.0-py3.6-nspkg.pth', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zope.interface-5.5.2.dist-info', '/usr/local/lib/python3.8/dist-packages')
            shutil.move('./fastapi_20_04/fastapi/lib/python3/dist-packages/zope.interface-5.5.2-py3.8-nspkg.pth', '/usr/local/lib/python3.8/dist-packages')


        shutil.move('./fastapi_20_04/fastapi/bin/dotenv' , '/usr/local/bin/dotenv')
        subprocess.call(['chmod', '777', '/usr/local/bin/dotenv'])
        shutil.move('./fastapi_20_04/fastapi/bin/uvicorn' , '/usr/local/bin/uvicorn')
        subprocess.call(['chmod', '777', '/usr/local/bin/uvicorn'])
        shutil.move('./fastapi_20_04/fastapi/bin/watchfiles' , '/usr/local/bin/watchfiles')
        subprocess.call(['chmod', '777', '/usr/local/bin/watchfiles'])

    elif ubuntu_version == '22.04':
        pass

    if not check_postgresql():
        print( 'CROWN2: [info] install postgresql') 
        if ubuntu_version == '18.04':
            subprocess.run('dpkg -i postgresql_18_04/*.deb', shell = True)
        elif ubuntu_version == '20.04':
            subprocess.run('dpkg -i postgresql_20_04/*.deb', shell = True)
        elif ubuntu_version == '22.04':
            pass
    else:
        print( 'CROWN2: [info] skip installing postgresql')
    subprocess.call(['chmod', '777', 'db_setting'])
    subprocess.run('./db_setting')
    if not check_redis():
        print( 'CROWN2: [info] install redis')
    else:
        print( 'CROWN2: [info] skip installing redis')
        if ubuntu_version == '18.04':
            subprocess.run('dpkg -i redis_18_04/*.deb', shell = True)
        elif ubuntu_version == '20.04':
            subprocess.run('dpkg -i redis_20_04/*.deb', shell = True)
        elif ubuntu_version == '22.04':
            pass
    register_service(install_path + os.sep + 'CROWN2')

if __name__ == "__main__":
    main(sys.argv)
