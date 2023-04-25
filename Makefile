# Docker operations
dev.build:
	docker-compose -f docker-compose.yml build $(c)
dev.up:
	docker-compose -f docker-compose.yml up -d $(c)
dev.down:
	docker-compose -f docker-compose.yml down $(c)
dev.destroy:
	docker-compose -f docker-compose.yml down -v $(c)
dev.stop:
	docker-compose -f docker-compose.yml stop $(c)
dev.restart:
	docker-compose -f docker-compose.yml restart $(c)
dev.logs:
	docker-compose -f docker-compose.yml logs --tail=100 -f $(c)
dev.shell:
	docker-compose -f docker-compose.yml exec web /bin/bash
dev.exec:
	@docker-compose -f docker-compose.yml exec web /bin/bash -c "poetry run $(cmd)"
dev.mongodb.shell:
	docker-compose -f docker-compose.yml exec mongodb /bin/bash -c 'mongosh -u ${MONGO_INITDB_ROOT_USERNAME} -p ${MONGO_INITDB_ROOT_PASSWORD} --authenticationDatabase admin'
dev.mongodb.drop:
	docker-compose -f docker-compose.yml exec mongodb /bin/bash -c 'mongosh -u ${MONGO_INITDB_ROOT_USERNAME} -p ${MONGO_INITDB_ROOT_PASSWORD} --authenticationDatabase admin --eval "use ${MONGO_INITDB_DATABASE}" --eval "db.dropDatabase()" --eval "show dbs"'

.PHONY: dev.build dev.up dev.down dev.destroy dev.stop dev.restart dev.logs dev.shell dev.exec dev.mongodb.shell dev.mongodb.drop
