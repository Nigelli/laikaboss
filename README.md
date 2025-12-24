
Laika BOSS: Object Scanning System
Laika is an object scanner and intrusion detection system that strives to achieve the following goals:

## Major changes from Lockheed Martin main tree
 
- Updates Lockheed Martin code from python 2 to python 3.
- Simple cluster deployment  using Docker
- Integrated mail server (Slimta)
- Authenticated Rest API and GUI 
- Moved from ZeroMQ to Redis for work queue
- Support multiple named queues and prioritized queuing
- Testing framework for modules
- It also includes SNL 15+ new written modules for parsing content this release,  along with the 30+ new modules released in 2020.
- Includes 3rd party open source LB modules written by others around the web – which haven’t (as of yet been) merged into LM’s tree
- Enhancements to LM and 3rd party modules based around attempted decrypting of compressed docs, and document formats using a known list of passwords and brute forcing passwords from text in the email message
 

### Currently unsupported/known issues

- No inline email blocking with integrated email server
- No Redis integration with Laikamilter/Sendmail
- Buffer bloat/on disk caching at each level causes latency
- Needs Kubernetes configuration/distribution - cluster is just deploying docker images across multiple systems
- Needs more framework and GUI tests

The underlying functionality of some modules and enhancements are based on other open-source packages - see the ADDITIONAL_LICENSES and requirements3.txt files for attribution/credit.
| Module                  | Description                                                                                                                                    | SNL Enhancements                                                                                                                                         | Source                      |
|:------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------|
| DISPOSITIONER           | Provides a definitive Accept or Deny                                                                                                           | includes disposition_reason in metadata                                                                                             | Upstream + Modifications    |
| EXPLODE_ACE             | Extracts ACE Compressed files                                                                                                                  |                                                                                                                                                          | SNL                         |
| EXPLODE_BINWALK         | File Carver                                                                                                                                    |                                                                                                                                                          | SNL                         |
| EXPLODE_BZ2             | Decodes BZ2 compressed files                                                                                                                   |                                                                                                                                                          | SNL                         |
| EXPLODE_CAB             | Explodes CAB files                                                                                                                             |                                                                                                                                                          | SNL                         |
| EXPLODE_EMAIL           |                                                                                                                                                | Improve support of per header encoded strings                                                                                                            | Upstream + Modifications    |
| EXPLODE_ENCRYPTEDOFFICE | Decodes Encrypted Office Docs                                                                                                                  | Flags that it was encrypted, Supports a list of passwords to try against the archive, supports trying all passwords in the text other included documents | SNL                         |
| EXPLODE_GZIP            | Extracts GZIP Compressed files                                                                                                                 | Adds bytelimits, filelimits and more metadata                                                                                                            | Upstream + Modifications    |
| EXPLODE_HEXASCII        | Converts hex encoded strings to ascii strings                                                                                                  |                                                                                                                                                          | SNL                         |
| EXPLODE_ISO             | Extracts files from ISO Files                                                                                                                  |                                                                                                                                                          | SNL                         |
| EXPLODE_MACHO           | Decodes Mac Executable Format - Mach-O and FAT files, and splits FAT files into seperate Mach-O files for further processing                   |                                                                                                                                                          | SNL                         |
| EXPLODE_MACRO           | Decompresses Office Macros                                                                                                                     | Detects Stomped PCODE (obfuscation Technique)                                                                                                            | SNL                         |
| EXPLODE_MSG             | Explode outlook MSG file                                                                                                                       |                                                                                                                                                          | SNL                         |
| EXPLODE_MULTIPARTFORM   | Explode key/value pairs from HTTP Multipart Forms                                                                                              |                                                                                                                                                          | SNL                         |
| EXPLODE_OFFICEXML       | Explode Office XML Encoded (WordML, *ML)                                                                                                       |                                                                                                                                                          | SNL                         |
| EXPLODE_OLE             |                                                                                                                                                | small bugfix                                                                                                                                             | Upstream                    |
| EXPLODE_OLENATIVE       | Alternate method of extracting OLE Objects                                                                                                     |                                                                                                                                                          | SNL                         |
| EXPLODE_PACKAGE         | MS Office                                                                                                                                      |                                                                                                                                                          | SNL                         |
| EXPLODE_PDF             | https://github.com/jshlbrd/laikaboss-modules                                                                                                   | Supports a list of passwords to try against the archive, supports trying all passwords in the text of documents                                          | Third Party + Modifications |
| EXPLODE_PDF_TEXT        | Extracts PDF Text Blobs from PDF's                                                                                                             | Supports a list of passwords to try against the archive, supports trying all passwords in the text of documents                                          | SNL                         |
| EXPLODE_PERSISTSTORAGE  | Extracting embedded objects within files - typically office documents which contain a shockwave flash file                                     |                                                                                                                                                          | SNL                         |
| EXPLODE_PKCS7           |                                                                                                                                                | small bugfix                                                                                                                                             | Upstream                    |
| EXPLODE_PLIST           | Apple Configuration Decoder                                                                                                                    |                                                                                                                                                          | SNL                         |
| EXPLODE_QR_CODE         | Extracts QR Codes                                                                                                                              |                                                                                                                                                          | SNL                         |
| EXPLODE_RAR2            | New version to replace upstream Explode_rar                                                                                                    | Support Decryption from a list of know passwords, or all items from extracted text structure                                                             | SNL                         |
| EXPLODE_RE_SUB          | Regex replace in buffers                                                                                                                       |                                                                                                                                                          | SNL                         |
| EXPLODE_RTF             |                                                                                                                                                |                                                                                                                                                          | SNL                         |
| EXPLODE_SEVENZIP        | Decodes 7zip compressed buffers                                                                                                                | Support Decryption from a list of know passwords, or all items from extracted text structure                                                             | SNL                         |
| EXPLODE_TAR             | Decodes tar buffers                                                                                                                            | Decodes metadata around file permissions                                                                                                                 | SNL                         |
| EXPLODE_TNEF            | Microsoftâ€™s Transport Neutral Encapsulation Decoder used by MS Exchange                                                                        |                                                                                                                                                          | SNL                         |
| EXPLODE_ZIP             | Extracts zip files                                                                                                                             | Support Decryption from a list of know passwords, or all items from extracted text structure                                                             | Upstream + Modifications    |
| LOG_SPLUNK              | Appends to a log file of results in JSON format                                                                                                |                                                                                                                                                          | SNL                         |
| LOOKUP_GEOIP            | Uses Geoip Lookup in Maxmind GeoLite2-City datatabase mmdb file                                                                                |                                                                                                                                                          | SNL                         |
| META_CRYPTOCURRENCY     | locates cryptocurrency addresses in text                                                                                                       |                                                                                                                                                          | SNL                         |
| META_DMARC              | Parses DMARC Files                                                                                                                             |                                                                                                                                                          | SNL                         |
| META_DOTNET             | Pulls out .net metadata from executables - https://github.com/cdiraimondi/laikaboss-modules                                                    | handles tmp files centrally for easier cleanup                                                                                                           | Third Party                 |
| META_EMF                | Parse Metadata from EMF Images                                                                                                                 |                                                                                                                                                          | SNL                         |
| META_EXIFTOOL           |                                                                                                                                                | Prefilter blacklist of fields to remove too much noise in results                                                                                        | Upstream + Modifications    |
| META_HTTPFORMGET        | Extract key/value pairs from a GET Form submission - decodesÂ the x-www-form-urlencoded format                                                  |                                                                                                                                                          | SNL                         |
| META_EMAIL              |                                                                                                                                                | Supports keeping track of header ordering, check if sent to spam mailbox, improved per header string decoding                                            | Upstream + Modifications    |
| META_IQY                | IQY - Link File Format                                                                                                                         |                                                                                                                                                          | SNL                         |
| META_ISO                | Extracts ISO files                                                                                                                             |                                                                                                                                                          | SNL                         |
| META_LNK                | Extracts data from windows shortcuts                                                                                                           | access, creation, and unique ids in metadata                                                                                                             | SNL                         |
| META_MACRO              | Extracts Metadata from Office Macro Files                                                                                                      |                                                                                                                                                          | SNL                         |
| META_MAGIC              | Extracts first few bytes of a buffer as hex into metadata                                                                                      |                                                                                                                                                          | SNL                         |
| META_OLE                | Extracts metadata about OLE files                                                                                                              | CLISD of all components                                                                                                                                  | SNL                         |
| META_ONENOTE            | Extracts Text, and Metadata from onenote files                                                                                                 |                                                                                                                                                          | SNL                         |
| META_OOXML_RELS         | Extracts Relationships from Office Open XML files                                                                                             |                                                                                                                                                          | SNL                         |
| META_OOXML_URLS         | Extracts Relationships from Office Open XML files                                                                                             |                                                                                                                                                          | SNL                         |
| META_PDF_STRUCTURE      | Extracts information from PDF's such as author, dimenstions of components, etc                                                                 |                                                                                                                                                          | SNL                         |
| META_PDFURL             | Extracts URL's from PDF's                                                                                                                      |                                                                                                                                                          | SNL                         |
| META_PE                 | Extracts metadata from PE's including hashes of all sections, and metadata                                                                     | hash PE Sections - compare against a known list of malicious PE Sections, symbols, Â and language                                                         | Upstream + Modifications    |
| META_PS_COMMANDS        | Extracts powershell Commands                                                                                                                   |                                                                                                                                                          | SNL                         |
| META_SCANINFO           | Keeps track of statistics about scans, including how long each scan took                                                                       |                                                                                                                                                          | SNL                         |
| META_TIFF               | Extracts Metadata about TIFF files, and sub TIFF files                                                                                         |                                                                                                                                                          | SNL                         |
| META_X509               | Extracts information about certificates                                                                                                        | Improve error handling, and extraction of components                                                                                                     | Upstream + Modifications    |
| META_ZIP                | Extracts info about zips suitable for zip file fingerprinting                                                                                  | Detects zipslip vunerbility, metasploit zip timestamp exploit,Â uses xyz                                                                                  | SNL                         |
| SCAN_HTML               | Extracts links, password fields, image anchors and display info, language, redirects, security policies, content-type, Percent Javascript, etc |                                                                                                                                                          | SNL                         |
| SCAN_YARA               | scans with yara                                                                                                                                | Provide String which matched for context, and offset in string                                                                                           | Upstream + Modifications    |
| SCAN_VBA                | Ole_tools vb tools - finds obfuscated strings                                                                                                  |                                                                                                                                                          | SNL                         |
| STORE_FILE              | Utility module for using dispatcher dumping only particular files to disk                                                                      |                                                                                                                                                          | SNL                         |
| SUBMIT_STORAGE_S3       | Submits sample, scan results, and Extracted files to storage in an S3 repository                                                               |                                                                                                                                                          | SNL                         |


## Description

 Laika is an object scanner and intrusion detection system that strives to achieve the following goals:

+ **Scalable**
	+ Work across multiple systems
	+ High volume of input from many sources
+ **Flexible**
	+ Modular architecture
	+ Highly configurable dispatching and dispositioning logic
	+ Tactical code insertion (without needing restart)
+ **Verbose**
	+ Generate more metadata than you know what to do with

Each scan does three main actions on each object:
+ **Extract child objects**

	Some objects are archives, some are wrappers, and others are obfuscators. Whatever the case may be, find children objects that should be scanned recursively by extracting them out.


+ **Mark flags**

	Flags provide a means for dispositioning objects and for pivoting on future analysis.


+ **Add metadata**

	Discover as much information describing the object for future analysis.

**Whitepaper can be found @ [http://lockheedmartin.com/us/what-we-do/information-technology/cybersecurity/laika-boss.html](http://lockheedmartin.com/us/what-we-do/information-technology/cybersecurity/laika-boss.html)**

## Deployment Options

This fork provides two deployment options:

### Core Scanner (ZeroMQ)
A lightweight, standalone scanner using the original ZeroMQ architecture. Ideal for:
- Simple deployments without external dependencies
- Drop-in replacement for the original Lockheed Martin laikaboss
- Users who don't need Redis, REST API, or web interface

```bash
# Build and run
docker compose -f docker-compose-core.yml build
docker compose -f docker-compose-core.yml up

# Scan a file
docker compose -f docker-compose-core.yml exec laikad \
  cloudscan.py -a tcp://localhost:5558 /home/laikaboss/workdir/yourfile
```

### Full Stack (Redis)
A complete deployment with Redis work queues, REST API, web GUI, mail server, and S3 storage. Ideal for:
- Enterprise deployments with multiple workers
- Web-based file submission and result viewing
- Email scanning pipelines
- Integration with Splunk and other logging systems

```bash
# Build and run
docker compose build
docker compose up
```

## Components
Laika is composed of the following pieces:

+ **Framework** (laika.py)

	This is the core of Laika BOSS. It includes the object model and the dispatching logic.

+ **laikad** (Core Scanner)

	Runs Laika as a daemonized, networked service using ZeroMQ. This is the original architecture from Lockheed Martin, now containerized with `docker-compose-core.yml`.

+ **laikadq** (Full Stack)

	Runs Laika as a daemon using Redis as a work queue. This is the architecture used by the full stack deployment.

+ **cloudscan**

	A command-line client for sending files to a running laikad instance (ZeroMQ).

+ **laikatest**
    A test framework for modules, run `./laikatest.py` to run all tests in the `tests` directory. Tests for some modules are included.

+ **laikarestd**
    This piece is an interface for submitting scans through a rest API. It also includes a web GUI for accessing scans stored in S3 buckets (in conjunction with the SUBMIT_STORAGE_S# module).


+ **laikacollector**
    This is a daemonized script for monitoring a directory and submitting files that are placed in it into a redis work queue (in conjunction with laikadq, which takes jobs out of redis and processes them).

+ **laikamail**
The Laika BOSS mail server can replace sendmail or postfix (and laikamilter) if you only run on copies of email and not inline. It is much simpler to manage.
```
+----------------+             +---------------+             +----------------+
|                | local disk  |               |             |                |
|    laikamail   +------------->laikacollector +------------>|     redis      |
|                |             |               |             |                |
+----------------+             +---------------+             +----------------+

             +-----------+
             |           |
<------------> laikadq 1 +
             |           |
             +-----------+

             +-----------+
             |           |
<------------> laikadq 2 +
             |           |
             +-----------+

             +-----------+
             |           |
<------------> laikadq N +
             |           |
             +-----------+

```

+ **modules**

	The scan itself is composed of the running of modules. Each module is its own program that focuses on a particular sub-component of the overall file analysis.

## Getting Started

### Quick Start - Core Scanner
The fastest way to get scanning is with the core scanner image:

```bash
# Clone the repo
git clone https://github.com/sandialabs/laikaboss.git
cd laikaboss

# Create a workdir for files to scan
mkdir -p workdir

# Build and start the scanner daemon
docker compose -f docker-compose-core.yml build
docker compose -f docker-compose-core.yml up -d

# Scan a file
cp /path/to/suspicious/file workdir/
docker compose -f docker-compose-core.yml exec laikad \
  cloudscan.py -a tcp://localhost:5558 /home/laikaboss/workdir/file | jq .

# Or run standalone (no daemon)
docker compose -f docker-compose-core.yml run --rm laikad \
  laika.py /home/laikaboss/workdir/file | jq .
```

### Quick Start - Full Stack
For the complete deployment with web GUI, REST API, and email scanning:

```bash
# Build and start all services
docker compose build
docker compose up -d

# Access the web GUI at https://localhost:8443
# Default credentials are in /etc/laikaboss/secrets/local_creds
```

See the detailed installation instructions below for production deployments.

### Writing New Modules
See the EXPLODE\_HELLOWORLD module (in `laikaboss/modules/explode_helloworld.py`) for an example of how to write a module.

### Running Standalone
From the directory containing the framework code, you may run the standalone scanner, laika.py against any file you choose. If you move this file from this directory you'll have to specify various config locations. By default it uses the configurations in the ./etc directory.

We recommend using [jq](http://stedolan.github.io/jq/) to parse Laika output.

##### Licensing
The Laika framework and associated modules are released under the terms of the Apache 2.0 license unless specified in the module or its dependencies

##### Quick install for cluster configuration
###### Prereqs

**Python Requirements:**
- **Python 3.8 or higher** (Python 3.10+ recommended)
- Tested on Python 3.8, 3.9, 3.10, and 3.11
- Python 3.6 is EOL and no longer supported

**System Requirements:**
1. Download the laikaboss source repo
1. Download the latest Docker and Docker-compose, do not use the OS default
1. install python3 package (Python 3.8+)
1. install pip for python3
1. pip3 install secrets future jinja2 passlib pyOpenSSL 
1. set up BCC from your border MTA to scan@your_laikaboss_email_server_domain

####### Install
1. Create local directories and accounts by calling
   (laikaboss src)/setup-host.sh
1. Download GeoLite2-City.mmdb from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
1. Put the file at location /etc/laikaboss/modules/geoip/GeoLite2-City.mmdb
1. Hand edit (laikaboss src)/etc/dist/laika_cluster.conf including all site specific changes
   In Docker make sure you uncomment the hostname and set hostname

   ```
    hostname = lbhost.example.com
    laika_head_node_short = lbhost
    laika_head_node = lbhost.example.com
    ldap_uri=ldaps://ldap.example.com:636
    ldap_account_base=ou=people,dc=example,dc=com
    ldap_group_attribute=memberOf
    ldap_group_base=ou=groups,dc=example,dc=com
    # if anon leave the value on the right side of the equal line blank
    ldap_auth_dn=cn=authuser,ou=people,dc=example,dc=com
    # if anon leave the value on the right side of the equal line blank
    ldap_auth_dn_pw=mypass123
    ldap_account_prefix=cn
    ldap_group_prefix=cn
    ldap_valid_groups=["group1", "group2", "group3"]

    LAIKA_AUTH_VALID_USERS=["laika_system"]
    ```
1. Copy etc/dist/laika_cluster.conf /etc/laikaboss/laika_cluster.conf
1. Run the script python3 (laikaboss src repo)/setup-secrets.py
    In addition to ldap authentication to the web GUI - you can use the default username and password generated in this file /etc/laikaboss/secrets/local_creds
1. Build the latest docker container(s)
```
   cd (source code repo)
      (source code repo)/env.sh
      (source code repo)/Docker/make-container3.sh
1. Build the latest apache container
   (source code repo)/env.sh
   (source code repo)/Docker/apache/make-container.sh
1. cd (source code repo)
1. docker compose up
1. Go to https://(yourhost):443 and login with your ldap username and password (or the default password in /etc/laikaboss/secrets/local_creds)
    * you will have to accept the self-signed cert which was issued
1. Change the env.sh image name to something you want to use at your site
1. Rebuild the LB and apache containers
1. Push docker images to a central repository hosted at your site so you can pull them down to other cluster nodes by name.
1. Modify the docker-compose.xml file to use the new image tags.

###### Post Configuration
1. Get a real certificate for your system and install it in /etc/laikaboss/secrets/server.crt and /etc/laikaboss/secrets/server.key in pem format, and /etc/laikaboss/secrets/cacert.crt (you can append multiple files into the same ca file)
   apache, redis, and the email server (for starttls) use the same path to the certificates - on different machines you can change the cert, but make sure the ca cert list has all of the needed certs.
1. Make sure docker is running on start up
   sudo systemctl enable docker 
1. Test the email service against your box hosting laikamail service - using s-nail/mailx examples: https://www.systutorials.com/sending-email-using-mailx-in-linux-through-internal-smtp/
   echo "test message" | s-nail -s "test app" -S smtp="127.0.0.1:25" -S from="test@example.com" scan@localhost   #(or scan@(fqhostname) - what the recipients param is set to in the configs"
1. Install a log monitoring agent and monitor file 
   /var/log/laikaboss/laikaboss_splunk.log
1. Set up a local firewall blocking open ports from off of the system or cluster
   Required ports available outside the cluster are 443(https), and port 25(smtp with start-tls)
   You could make port 9002 available if you wish to make minio accessible directly
   Within the cluster port 9002(minio S3 and minio GUI), 443(https), 6379(redis over SSL)
1. On redundant servers you must copy the /etc/laikaboss folder including any relevant keys/password etc in /etc/laikaboss/secrets, make sure you run the setup-host.sh script to create any missing directories and file permissions.
1. Create at least 2 servers which handle mail for redundancy - these servers can be co-located with any of the other services
   - SMTP is the most important box for redundancy - because if SMTP is down, it will CAUSE email bounces back to your site MTA - which often bounce back to the orig email sender. 
   The docker compose file for an email/SMTP boxes only needs to contain the services laikamail and laikacollector
1. If you need a non-ldap account to log into the system - the user laika_system is enabled by default in the laika_cluster.conf file. The randomly generated password is located in this file /etc/laikaboss/secrets/local_creds - it is also used by the newness module.  You can change the attribute below to just point to an empty JSON list of [].
LAIKA_AUTH_VALID_USERS=["laika_system"]
1. Optional:  Install multiple laikadq worker hosts - they only need to have the services laikadq and submitstoraged installed.  They need to be able to talk to redis, and the S3 server, and the webservice endpoints on laikarestd/apache.
1. Configure your primary email server to send BCC emails to scan@(your host) on your mail hosts.  If your host is wrong, it may decline the email per the ACL's set in laika_cluster.conf file
1. docker-compose up -d
###### USEFUL tips
1. Test the email service against your box hosting laikamail service - using s-nail/mailx examples: https://www.systutorials.com/sending-email-using-mailx-in-linux-through-internal-smtp/
`echo "test message" | s-nail -s "test app" -S smtp="127.0.0.1:25" -S from="test@example.com" scan@localhost   #(or scan@(fqhostname) - what the recipients param is set to in the configs"`
1.  Debugging steps
    1. Is the mail server up and listening from off the host - it will immediate come back if it can't connect hit control+] to exit if a connection succeeds or with netcat
       ``` 
       telnet lbmailsersver 25
       nc -zv lbmailserver 22
       ```
    1. Look for dead containers or containers which keep getting restarted
       ```
       docker container ls -f 'status=exited' -f 'status=dead' -f 'status=created'
       docker container ls -l
       ```
    1. Make sure the containers are running needed to accept and submit mail. Grab the submitID of the message and the name of the submission file 
       ```
       docker-compose container ls laikamail
       docker-compose container ls laikacollector
       ```
    1. Check the submission queue and error directories
       ```
       /data/laikaboss/submission-queue/email 
       /data/laikaboss/submission-error/
       ```
    1. Do the storage and redis servers work - submit a file to the GUI for scanning on the laikarestd/GUI host OR just sanity check storage and queue services and look for dead containers - make sure the containers are running needed to process the sample
       ```
       docker container ls -f 'status=exited' -f 'status=dead' -f 'status=created'`
       docker-compose container ls laikarestd # used for REST submissions including GUI, and newess
       docker-compose container ls laikacollector # used for REST submissions including GUI, and newess
       docker-compose container ls storage # used for s3 file storage 
       docker-compose container ls redis # used for all sync and sync cluster scanning, and newness cache
       ```
    1. Check their logs next using the log directory above and check the submission queue and error directories - Check their logs next using the log directory - grab the submitID of the sample and the name of the submission file 
       ```
       /data/laikaboss/submission-queue/WebUI
       /data/laikaboss/submission-error/
       ```
    1. Are workers processing your work
       ```
       docker-compose container ls laikadq
       docker-compose container ls submitstoraged # only if its a storage issue
       ```
    1. Check their logs next using the log directory above - lookup the submitID and or filename of sample - use this to find the rootUID
       Check the logs for the rootUID to track where it fails
    1. Is the log being created.
       Check the output logs for summary=False, and possibly summary=True entries by RootUID
    1. Is your splunk forwarder agent running and able to read the log files  
       Check /opt/splunkforwarder/var/log/splunk.log
    1. Check splunk logs by the necessary index in splunk by using the rootUID
    1. Check the gui by looking up the rootUID in the GUI
###### MAINTENANCE
1. A sample requirements3.txt has been included which pins modules to known working versions.  
   To update it - you'll need to mount the source code in a container and recreate it - with the latest versions.
   ```
   . (source code repo)/env.sh
   go into the container by running the command below
   docker-compose run -it laikadq /bin/bash'
   update the dependencies
   cd /var/laikaboss/run; pip-compile --output-file=requirements3.txt requirements3.in`
   docker container ls -a # get your relevant (latest?) container id
   docker cp <container id>:/var/run/laikaboss/requirements.txt <container id>:/var/run/laikaboss/requirements3.txt <path to your source code repo>
   ```
   for a major updates in packages or OS's also use the --upgrade flag
   Then after rebuilding the container rerun the tests      
   `docker-compose run laikadq -t`
2. Set up some log rotation scripts
3. Keep an eye on submission, error or storage directories have too many items
4. Disk filling
5. Email bouncing to client - this can happen if laikaboss email servers are inaccessible, or you cc'd to the wrong name - you want rules in the upstream MTA to prevent bounces going to senders on the internet!  Also have at least 1 redundant smtp server in laikaboss on another host
