scp -i "visionai.pem" -r G:\Desktop\visionai\frontend\* ubuntu@13.51.158.58:/tmp/frontend/

then 

ssh -i "visionai.pem" ubuntu@13.51.158.58

Then

sudo cp -r /tmp/frontend/* /var/www/visionai/

scp -i "visionai.pem" -r G:\Desktop\visionai\browser-automation\* ubuntu@13.51.158.58:/home/ubuntu/browser-automation
