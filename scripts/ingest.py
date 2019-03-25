import os
import subprocess
import sys

os.system('scp C:/PROJECTS/Directed_Studies/XML_Test_Data/Outputs/gbl/* scoadmin@144.92.235.110:gbl_metadata')

HOST="144.92.235.110"
# Ports are handled in ~/.ssh/config since we use OpenSSH
COMMAND="mv gbl_metadata/*.json gbl_metadata/transfer/"

ssh = subprocess.Popen(["ssh", "-i", "H:\.ssh\id_rsa", 'scoadmin@144.92.235.110', COMMAND],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
result = ssh.stdout.readlines()
if result == []:
    error = ssh.stderr.readlines()
    print >>sys.stderr, "ERROR: %s" % error
else:
    print result