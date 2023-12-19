import os

banned_ips: list[str] = []

if (not os.path.exists("BannedIPs.txt")):
    with open("BannedIPs.txt", "w+") as f:
        f.close()

def ReloadBannedIPs() -> None:
    banned_ips = []

    with open("BannedIPs.txt", "r") as f:
        for b_ip in f.readlines():
            if (len(b_ip.strip()) == 0):
                continue

            banned_ips.append(b_ip.strip())

        f.close()

def SaveIPs() -> None:
    with open("BannedIPs.txt", "w+") as f:
        b_ips_t = ""

        for b_ip in banned_ips:
            b_ips_t += b_ip + "\n"
        
        f.write(b_ips_t)
        f.close()

def BanIP(ip: str) -> bool:
    if (banned_ips.count(ip) == 0):
        banned_ips.append(ip)
        SaveIPs()
        ReloadBannedIPs()

        return True
    
    return False

def UnbanIP(ip: str) -> bool:
    if (banned_ips.count(ip) > 0):
        banned_ips.remove(ip)
        SaveIPs()
        ReloadBannedIPs()

        return True
    
    return False

def IsIPBanned(ip: str) -> bool:
    ReloadBannedIPs()
    return banned_ips.count(ip) > 0

ReloadBannedIPs()