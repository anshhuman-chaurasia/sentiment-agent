# Setup Guide for OCI Always Free Tier

This guide walks you through setting up this Stock Sentiment Agent on a fresh Oracle Cloud Infrastructure (OCI) instance using the Always Free tier.

## 1. Create the OCI Instance

1. Log into your OCI Console.
2. Go to **Compute -> Instances** and click **Create Instance**.
3. **Name:** `sentiment-agent-vm`
4. **Image and Shape:**
   - Click *Edit*.
   - **Image:** Canonical Ubuntu 22.04 (or Oracle Linux).
   - **Shape:** Select `Ampere` (ARM) -> `VM.Standard.A1.Flex`. Choose 1 OCPU and at least 4 GB (up to 24 GB) of RAM. This is part of the Always Free tier.
5. **Networking:**
   - Select an existing VCN or let it create a new one. Ensure it assigns a public IPv4 address.
6. **SSH Keys:** Save the generated private key or upload your public key.
7. Click **Create**.

## 2. Configure VCN Security List (Firewall)

To access the API and Dashboard from your browser, you must open ports `8000` and `8501`.

1. In the OCI Console, navigate to your instance details and click on the **Subnet**.
2. Click on the **Security List** associated with the subnet.
3. Click **Add Ingress Rules**:
   - **Source CIDR:** `0.0.0.0/0` (or restrict to your IP)
   - **IP Protocol:** TCP
   - **Destination Port Range:** `8000, 8501`
   - **Description:** Allow FastAPI and Streamlit
4. Click **Add Ingress Rules**.

*(Note: On Ubuntu, you must also allow these ports through `iptables`. See below).*

## 3. SSH and Prepare the Instance

SSH into your new instance:
```bash
ssh -i /path/to/private.key ubuntu@<YOUR_INSTANCE_PUBLIC_IP>
```

Open the OS firewall ports:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8501 -j ACCEPT
sudo netfilter-persistent save
```

Install Docker and Docker Compose:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```
*(Log out and log back in to apply the docker group changes).*

## 4. Deploy the Application

Clone this repository to your instance:
```bash
git clone <YOUR_REPO_URL>
cd sentiment-agent
```

Run the application stack using Docker Compose:
```bash
docker-compose up -d --build
```

Docker will build the image, download the dependencies (and the FinBERT model on first run), and start the services.

## 5. Verify the Deployment

- **API:** Visit `http://<YOUR_INSTANCE_PUBLIC_IP>:8000/docs` to see the interactive API documentation.
- **Dashboard:** Visit `http://<YOUR_INSTANCE_PUBLIC_IP>:8501` to access the Streamlit UI.

## (Optional) Connect to Oracle Autonomous Database

If you want to use the Always Free Autonomous Database instead of SQLite:
1. Create an Autonomous Database (Transaction Processing) in OCI.
2. Download the Regional Wallet.
3. Update `docker-compose.yml` to uncomment the `DB_URL` line and set it to:
   `oracle+oracledb://<username>:<password>@<tns_name>?config_dir=/app/wallet`
4. Mount the wallet directory into your Docker container.