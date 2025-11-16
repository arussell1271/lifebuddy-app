# Helpful Docker Commands





### Containers



##### Stopping All Containers



docker compose stop



This command **stops** all services but **leaves the containers, networks, and volumes in place**. This is the safest way to ensure your database volume (dev\_postgres\_data) is no longer being written to, making it ready for a reliable backup.





##### Shutdown Containers



###### Shutdown and Removes Orphans

docker compose down --remove-orphans



The --remove-orphans flag ensures any container that was started but is no longer defined in your docker-compose.yml (like a container that may be holding the network lock) is also stopped and removed, often leading to a cleaner shutdown.

