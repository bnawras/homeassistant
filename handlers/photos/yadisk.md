# Yandex.Disk REST API How To (quick af)

> This will be modified, don't worry

## 1. Register
Simply make standard account on `disk.yandex.com`

## 2. Register App Client
First thing to do is to register new App Client. This can be done in `oauth.yandex.com`.
 - Click on "Create new client" button
 - Enter "App Name"
 - Apply permissions you want for "Yandex.Disk REST API" (if you dont know which permissions you want, select all of them)
 - Click "Create App" button
 
## 3. Get OAuth token for App Client
Now you need to get OAuth token for your client. This can be done by going to `https://oauth.yandex.com/authorize?response_type=token&client_id=(Here your ID from registering app website)`. **You should enter this site by browser, not curl!**

## 4. Test request your files (List files)
From now on, refer to Yandex.Disk REST API documentation at `https://tech.yandex.com/disk/api/concepts/about-docpage/`

With every request, you have to add your oauth token via `Authorization` header. Here's example for file list request:
```bash
curl --header "Authorization: OAuth (Here_Your_Token)" https://cloud-api.yandex.net/v1/disk/resources/files
```

# Quick reference
## A. Uploading file
```bash
Token=(Your token here)
# Request an upload URL
curl --header "Authorization: OAuth $Token" https://cloud-api.yandex.net/v1/disk/resources/upload?path=FILENAME&overwrite=false

# Upload file to specified URL
curl -F "file=@Your_Local_File.txt" --header "Authorization: OAuth $Token" (Upload URL from Request)
```

## B. Download file
```bash
Token=(Your token here)
# Request an upload URL
curl --header "Authorization: OAuth $Token" https://cloud-api.yandex.net/v1/disk/resources/download?path=FILENAME

# Download file
wget (Download URL from request)
```