wacs.exe `
  --target manual `
  --host "example.com" `
  --validationmode dns-01 `
  --validation script `
  --dnscreatescript "vd-dns.ps1" `
  --dnscreatescriptarguments `
    "--config app-config.ini --domain {ZoneName} --record-name {RecordName} --token {Token}" `
  --store pemfiles `
  --pemfilespath .\certs `
  --accepttos `
  --emailaddress you@example.com
