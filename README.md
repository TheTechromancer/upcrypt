upcrypt.py
==============

Batch encrypt files using 7zip (AES-256)
--------------

Upcrypt is a simple python script which wraps p7zip and makes it easy to encrypt large amounts of files individually (while preserving their folder structure).  The script is not necessary to *decrypt*; 7-zip or p7zip by themselves will work just fine.

Typical use case:

- Uploading a large number of files to untrusted cloud service, but must have the ability to access them on an individual basis.

This prevents the need to extract the entire archive when accessing a single file, and saves you from having to encrypt each file individually.

Usage:
----------

  upcrypt.py [-h] [-d] -p PASS [-o DIR] [-w] [-t INT] [--split SIZE] [-v] [FILES [FILES ...]]

  Batch-encrypts files using 7-zip. To 'process' means to encrypt or decrypt,
  depending on which it's doing.

  positional arguments:
    FILES                 Files or directories to process

  optional arguments:
    -h, --help               show this help message and exit  
    -d, --decrypt            Decrypt rather than encrypt  
    -p PASS, --password PASS Password to use for encryption/decryption  
    -o DIR, --out-dir DIR    Where to put processed files  
    -w, --wrap               Zip contents into single file (don't encrypt individually)  
    -t INT, --threads INT    Number of CPU cores to use. Default is all.  
    --split SIZE             Split into volumes of SIZE. Default is None. Useful for circumventing filesize limitations. ;)  
    -v, --verbose            Print what is happening. (limits threads to 1)  
