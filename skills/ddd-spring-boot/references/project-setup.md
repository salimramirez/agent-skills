# Project setup

What the `pom.xml`, the properties and the application class look like before the first context goes in.

Start from the Spring Initializr with Spring Web, Spring Data JPA, Validation, Lombok, the MySQL driver and DevTools. Then add what the house style needs and what the shared kernel expects.

## `pom.xml`

Beyond the Initializr defaults, these dependencies:

```xml
<!-- Table names as plural snake_case: used by the naming strategy in the shared kernel -->
<dependency>
    <groupId>io.github.encryptorcode</groupId>
    <artifactId>pluralize</artifactId>
    <version>1.0.0</version>
</dependency>
<!-- OpenAPI description and Swagger UI at /swagger-ui.html -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.13</version>
</dependency>
```

Lombok needs the annotation-processor entry the Initializr already writes into `maven-compiler-plugin`, and the exclusion in `spring-boot-maven-plugin`, so it never ships in the jar:

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <configuration>
        <annotationProcessorPaths>
            <path>
                <groupId>org.projectlombok</groupId>
                <artifactId>lombok</artifactId>
            </path>
        </annotationProcessorPaths>
    </configuration>
</plugin>
```

The IAM context adds Spring Security, `jjwt` and `commons-lang3`; `iam.md` lists them. On Spring Boot 4 the web starter is `spring-boot-starter-webmvc` instead of `spring-boot-starter-web`; nothing else in this setup changes between the two.

## `application.properties`

One file with what does not change between environments, one per profile with what does. The active profile comes from the environment, so the same jar runs everywhere:

```properties
# Spring Application Name
spring.application.name=QuickBite Platform

# Profile
spring.profiles.active=${SPRING_PROFILES_ACTIVE}

# Spring DataSource Configuration
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver

# Spring Data JPA Hibernate Configuration
spring.jpa.hibernate.ddl-auto=update
spring.jpa.open-in-view=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQLDialect
spring.jpa.hibernate.naming.physical-strategy=com.quickbite.platform.shared.infrastructure.persistence.jpa.configuration.strategy.SnakeCaseWithPluralizedTablePhysicalNamingStrategy

# Application Information for Documentation
# Elements take their values from maven pom.xml build-related information
documentation.application.description=@project.description@
documentation.application.version=@project.version@
```

`application-dev.properties`:

```properties
spring.datasource.url=jdbc:mysql://localhost:3306/quickbite?useSSL=true&serverTimezone=UTC&createDatabaseIfNotExist=true&publicKeyRetrieval=true
spring.datasource.username=root
spring.datasource.password=${QUICKBITE_MYSQL_PWD}
spring.jpa.show-sql=true
```

`application-prod.properties` has the real host, `show-sql=false`, and every credential read from the environment. Run locally with `SPRING_PROFILES_ACTIVE=dev QUICKBITE_MYSQL_PWD=… ./mvnw spring-boot:run`.

Three of these lines carry a decision worth knowing:

- **`ddl-auto=update`** lets Hibernate create and alter tables from the entities, which is what makes the first run of a new context work with no migration. It is a development convenience: it never drops a column and never renames one, so once a schema is in production, migrations take over.
- **`open-in-view=true`** (the Spring Boot default, made explicit) keeps the persistence context open for the whole request. The assemblers depend on it: they walk lazy collections such as an order's lines from inside the controller, and with `open-in-view=false` that walk throws `LazyInitializationException`. Keep it on unless every assembler is fed fully-loaded aggregates.
- **The naming strategy** turns `OrderLine.menuItemId` into `order_lines.menu_item_id`. Table names are plural on purpose: a table holds many of the thing, and it also keeps `Order` — a reserved word in SQL — from ever becoming a table name.

## The application class

```java
@SpringBootApplication
@EnableJpaAuditing
public class QuickBitePlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(QuickBitePlatformApplication.class, args);
    }

}
```

`@EnableJpaAuditing` is what fills `createdAt` and `updatedAt` on every aggregate; without it, the base class's `@Column(nullable = false)` on those fields makes the first insert fail. The base package of this class is what the scripts use to place the code they generate.

## Where it shows up

Once running: the API under `/api/v1/…`, its description at `/v3/api-docs`, and Swagger UI at `/swagger-ui.html`, with the title, description and version taken from the properties above.
