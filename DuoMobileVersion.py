import base64, email.utils, hmac, hashlib, requests, urllib, csv


ADMIN_IKEY = input('Please enter your Admin API IKEY: ')
ADMIN_SKEY = input('Please enter your Admin API SKEY: ')
API_HOSTNAME = input('Please enter your API hostname: ')


class VersionPuller:
    def __init__(self, ADMIN_IKEY,ADMIN_SKEY, API_HOSTNAME):
        self.ADMIN_IKEY = ADMIN_IKEY
        self.ADMIN_SKEY = ADMIN_SKEY
        self.API_HOSTNAME = API_HOSTNAME
        self.METHOD = "GET"
        self.API_PATH = "/admin/v1/phones"
        self.LIMIT = 500
        self.PARAMS = {"offset":0 ,"limit":self.LIMIT}
        self.URL = f'https://{self.API_HOSTNAME}{self.API_PATH}'
        self.PHONELIST = []
        self.PARSEDDIC = {}
    def sign(self):
        # create canonical string
        now = email.utils.formatdate()
        canon = [now, self.METHOD, self.API_HOSTNAME, self.API_PATH]
        args = []
        for key in sorted(self.PARAMS.keys()):
            val = self.PARAMS[key].encode("utf-8")
            args.append(
                '%s=%s' % (urllib.parse.
                           quote(key, '~'), urllib.parse.quote(val, '~')))

        canon.append('&'.join(args))
        canon = '\n'.join(canon)
        # sign canonical string
        sig = hmac.new(bytes(self.ADMIN_SKEY, encoding='utf-8'),
                       bytes(canon, encoding='utf-8'),
                       hashlib.sha1)
        auth = '%s:%s' % (self.ADMIN_IKEY, sig.hexdigest())
        # return headers
        return {'Date': now, 'Authorization': 'Basic %s' % base64.b64encode(bytes(auth, encoding="utf-8")).decode()}


    def getPhones(self):

        while self.PARAMS["offset"] != -1 :

            self.PARAMS["offset"] = str(self.PARAMS["offset"])
            self.PARAMS["limit"] = str(self.LIMIT)
            headers = self.sign()
            response = requests.get(self.URL, headers=headers, params=self.PARAMS)
            content = response.json()
            try:
                nextOffset = content["metadata"]["next_offset"]
                self.PARAMS["offset"] = nextOffset
            except KeyError:
                self.PARAMS["offset"] = -1

            if content.get("response"):
                content = content["response"]

                for phone in content:
                    if phone["app_version"] != "" :
                        self.PHONELIST.append(phone)
                    else:
                        continue

    def parser(self):
        for phone in self.PHONELIST:
            version = phone["app_version"]
            if int(version[:1]) == 3 or int(version[:1]) == 2 or int(version[version.index(".")+1:version.index(".", 2)]) < 85:
                users = []
                for user in phone["users"]:
                    users.append(user["email"])
                    self.PARSEDDIC[phone["phone_id"]] = [phone["app_version"],phone["number"],phone["last_seen"], users]
    def CSVwriter(self):
        with open("user list.csv", "w") as csvFile:
            fieldnames = ["App Version", "Phone Number", "Last Seen", "Attached User(s)"]
            writer = csv.DictWriter(csvFile,fieldnames)
            writer.writeheader()
            for phone in self.PARSEDDIC.values():
                writer.writerow({"App Version":phone[0], "Phone Number":phone[1], "Last Seen":phone[2], "Attached User(s)":phone[3]})
        print("List writen to user_list.csv")


def main():
    phones = VersionPuller(ADMIN_IKEY,ADMIN_SKEY,API_HOSTNAME)
    phones.getPhones()
    phones.parser()
    phones.CSVwriter()

main()

