# Package structure: the four layers

The package tree for a bounded context, and what belongs in each layer.

Give each **bounded context** its own package, split into the four layers, with dependencies pointing inward toward `domain`. A common, consistent layout:

```
com.quickbite.ordering
├── interfaces                     // inbound adaptors — the outside drives the context
│   ├── rest
│   │   ├── controllers            // REST controllers
│   │   ├── resources              // request/response DTOs (records)
│   │   └── transform              // assemblers: resource <-> command / entity
│   └── acl                // facade this context exposes to other contexts
├── application                    // use-case orchestration (no business rules)
│   ├── acl                    // this context's facade implementation
│   └── internal
│       ├── commandservices    // command service implementations
│       ├── queryservices      // query service implementations
│       ├── eventhandlers      // react to domain events
│       └── outboundservices
│           └── acl            // talk to other contexts through their facades
├── domain                         // the domain model + its ports (depends on nothing)
│   ├── model
│   │   ├── aggregates
│   │   ├── entities
│   │   ├── valueobjects
│   │   ├── commands       // command types (domain)
│   │   ├── queries        // query types (domain)
│   │   └── events         // domain events
│   ├── services           // command/query service interfaces (ports)
│   └── exceptions         // domain-specific exceptions
└── infrastructure                 // outbound adaptors — the context reaches out
    └── persistence
        └── jpa
            └── repositories       // Spring Data repositories
```

**What each layer is** (dependencies always point inward, toward `domain`):

- **`interfaces` — inbound adaptors.** Where the outside world drives this context: REST controllers, message/event listeners, a CLI. They turn external input into application calls and shape the response back out. No business logic.
- **`application` — application services.** They orchestrate use cases (here split into command and query services): load aggregates, invoke their behavior, manage transactions and security. They coordinate but hold no business rules.
- **`domain` — the domain model.** Aggregates, entities, value objects, domain events, the service *interfaces* (ports), and domain exceptions. Every business rule lives here, and it depends on nothing outside itself.
- **`infrastructure` — outbound adaptors.** The technical pieces the context uses to reach external systems: the Spring Data repositories, message publishers, external API clients. They implement any ports the inner layers declare.

**Inbound vs. outbound adaptor** describes the direction of flow. An *inbound* adaptor brings a request *into* the context — e.g., a controller turning an HTTP call into a command. An *outbound* adaptor lets the context reach *out* to something external — e.g., a repository writing to the database, or an ACL service calling another context. The domain in the middle never knows about either: the inner layers declare **ports** (interfaces), and the adaptors implement them.
