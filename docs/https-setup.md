# HTTPS Setup (LAN Access)

## Prerequisites
- mkcert (`brew install mkcert`)
- Caddy (`brew install caddy`)

## First-time setup
1. `mkcert -install` (installs local CA -- requires sudo, run manually in terminal)
2. `cd certs && mkcert <your-ip> localhost 127.0.0.1`
3. Update Caddyfile with your IP and cert filenames

## Running
Start backend and frontend as usual, then:
```bash
cd /Users/ajinkya/work/audio-story-creator
caddy run
```
Access at `https://<your-ip>`

## Notes
- The `certs/` directory is gitignored -- never commit certificates.
- If your local IP changes, regenerate certs and update the Caddyfile.
- Other devices on the same WiFi need to trust the local CA. You can find the CA cert with `mkcert -CAROOT` and install it on those devices.
