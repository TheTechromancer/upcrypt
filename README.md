upcrypt.py
==============

Batch encrypt files using 7zip (AES-256)
--------------

Upcrypt is a simple python script which wraps p7zip and makes it easy to encrypt large amounts of files individually.  The script is not necessary to *decrypt*; 7-zip or p7zip by themselves will work just fine.

Typical use case:

- Uploading large amounts of files to an untrusted cloud service, but need to access them on an individual basis.

This prevents the need to extract the entire archive when accessing a single file, and saves you from having to encrypt each file individually.
