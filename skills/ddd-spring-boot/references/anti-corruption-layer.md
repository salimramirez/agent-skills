# Anti-corruption layer

Reaching another bounded context through a facade, without letting its model in.

When this context needs something from **another** bounded context, do not import its model. The provider context exposes a **facade interface** (in its `interfaces/acl`) and implements it in `application/acl`, returning only primitives or ids — never its own domain types. The consumer calls that facade through an **outbound ACL service** that translates the result into *its own* value objects. This is the strategic anti-corruption layer, realized in code.

```java
// Customer context exposes — customer/interfaces/acl
public interface CustomerContextFacade {
    Long fetchCustomerIdByEmail(String email);
}

// Customer context implements — customer/application/acl
@Service
public class CustomerContextFacadeImpl implements CustomerContextFacade {
    private final CustomerQueryService customerQueryService;
    public CustomerContextFacadeImpl(CustomerQueryService customerQueryService) {
        this.customerQueryService = customerQueryService;
    }
    @Override
    public Long fetchCustomerIdByEmail(String email) {
        return customerQueryService.handle(new GetCustomerByEmailQuery(email))
            .map(Customer::getId).orElse(0L);   // 0 signals "not found" across the boundary
    }
}

// Ordering context consumes — ordering/application/internal/outboundservices/acl
@Service
public class ExternalCustomerService {
    private final CustomerContextFacade customers;
    public ExternalCustomerService(CustomerContextFacade customers) { this.customers = customers; }

    public Optional<CustomerId> fetchCustomerByEmail(String email) {
        var id = customers.fetchCustomerIdByEmail(email);
        return id == 0L ? Optional.empty() : Optional.of(new CustomerId(id));  // translate to our VO
    }
}
```
