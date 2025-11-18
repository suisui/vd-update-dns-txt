wacs.exe `
  --target manual `
  --host "example.com" `
  --validationmode dns-01 `
  --validation script `
  --dnscreatescript ".\vd-dns.ps1" `
  --dnscreatescriptarguments `
    " ""app-config.ini"" ""{ZoneName}"" ""{RecordName}"" ""{Token}"" " `
  --store pemfiles `
  --pemfilespath .\certs `
  --accepttos `
  --emailaddress you@example.com
