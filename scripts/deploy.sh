#!/bin/bash

set -x  # Activer le mode débogage pour afficher chaque commande exécutée

KEY_PATH="./doc/NicoDocker.pem"
INSTANCE_USER="ec2-user"
INSTANCE_IP="ec2-13-60-61-142.eu-north-1.compute.amazonaws.com"
PROJECT_PATH="../kconvertor-server"
REMOTE_PATH="/home/ec2-user/kconvertor-server"
DOCKER_IMAGE_NAME="kconvertor-server"

# 1. Mise à jour du système et installation de Docker
echo "=== Update of Docker ==="
ssh -i "$KEY_PATH" -tt -o StrictHostKeyChecking=no $INSTANCE_USER@$INSTANCE_IP << 'EOF'
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
exit
EOF

if [ $? -ne 0 ]; then
  echo "Erreur lors de la mise à jour du système ou l'installation de Docker"
  exit 1
fi

# 2. Copier le projet vers l'instance EC2
echo "=== Copy project into EC2 instance ==="
scp -i "$KEY_PATH" -r "$PROJECT_PATH" $INSTANCE_USER@$INSTANCE_IP:$REMOTE_PATH

if [ $? -ne 0 ]; then
  echo "Erreur lors de la copie du projet"
  exit 1
fi

# 3. Construire et exécuter le conteneur Docker
echo "=== Create and launch Docker image ==="
ssh -i "$KEY_PATH" -tt -o StrictHostKeyChecking=no $INSTANCE_USER@$INSTANCE_IP << EOF
cd $REMOTE_PATH
sudo docker build -t $DOCKER_IMAGE_NAME .
sudo docker run -d -p 5000:5000 $DOCKER_IMAGE_NAME
exit
EOF

if [ $? -ne 0 ]; then
  echo "Erreur lors de la construction et du lancement du conteneur Docker"
  exit 1
fi

# 4. Fin du script
echo "=== Deployed on: http://$INSTANCE_IP:5000 ==="

set +x  # Désactiver le mode débogage
