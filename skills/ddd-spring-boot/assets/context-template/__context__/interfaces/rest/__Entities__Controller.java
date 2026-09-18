package __base_package__.__context__.interfaces.rest;

import __base_package__.__context__.domain.model.commands.Delete__Entity__Command;
import __base_package__.__context__.domain.model.queries.GetAll__Entities__Query;
import __base_package__.__context__.domain.model.queries.Get__Entity__ByIdQuery;
import __base_package__.__context__.domain.services.__Entity__CommandService;
import __base_package__.__context__.domain.services.__Entity__QueryService;
import __base_package__.__context__.interfaces.rest.resources.Create__Entity__Resource;
import __base_package__.__context__.interfaces.rest.resources.Update__Entity__Resource;
import __base_package__.__context__.interfaces.rest.resources.__Entity__Resource;
import __base_package__.__context__.interfaces.rest.transform.Create__Entity__CommandFromResourceAssembler;
import __base_package__.__context__.interfaces.rest.transform.Update__Entity__CommandFromResourceAssembler;
import __base_package__.__context__.interfaces.rest.transform.__Entity__ResourceFromEntityAssembler;
import __base_package__.shared.interfaces.rest.resources.MessageResource;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static org.springframework.http.MediaType.APPLICATION_JSON_VALUE;

/**
 * __Entities__Controller
 * <p>
 *     All __entity__ related endpoints.
 * </p>
 */
@RestController
@RequestMapping(value = "/api/v1/__entities-kebab__", produces = APPLICATION_JSON_VALUE)
@Tag(name = "__Entities__", description = "Available __Entity__ Endpoints")
public class __Entities__Controller {
    private final __Entity__CommandService __entity__CommandService;
    private final __Entity__QueryService __entity__QueryService;

    /**
     * Constructor
     *
     * @param __entity__CommandService The {@link __Entity__CommandService} instance
     * @param __entity__QueryService   The {@link __Entity__QueryService} instance
     */
    public __Entities__Controller(__Entity__CommandService __entity__CommandService, __Entity__QueryService __entity__QueryService) {
        this.__entity__CommandService = __entity__CommandService;
        this.__entity__QueryService = __entity__QueryService;
    }

    /**
     * Create a new __entity__
     *
     * @param resource The {@link Create__Entity__Resource} instance
     * @return The {@link __Entity__Resource} resource for the created __entity__
     */
    @PostMapping
    @Operation(summary = "Create a new __entity__", description = "Create a new __entity__")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "__Entity__ created"),
            @ApiResponse(responseCode = "400", description = "Invalid input")})
    public ResponseEntity<__Entity__Resource> create__Entity__(@RequestBody Create__Entity__Resource resource) {
        var create__Entity__Command = Create__Entity__CommandFromResourceAssembler.toCommandFromResource(resource);
        var __entity__Id = __entity__CommandService.handle(create__Entity__Command);
        if (__entity__Id == null || __entity__Id == 0L) return ResponseEntity.badRequest().build();
        var get__Entity__ByIdQuery = new Get__Entity__ByIdQuery(__entity__Id);
        var __entity__ = __entity__QueryService.handle(get__Entity__ByIdQuery);
        if (__entity__.isEmpty()) return ResponseEntity.notFound().build();
        var __entity__Entity = __entity__.get();
        var __entity__Resource = __Entity__ResourceFromEntityAssembler.toResourceFromEntity(__entity__Entity);
        return new ResponseEntity<>(__entity__Resource, HttpStatus.CREATED);
    }

    /**
     * Get __entity__ by id
     *
     * @param __entity__Id The __entity__ id
     * @return The {@link __Entity__Resource} resource for the __entity__
     */
    @GetMapping("/{__entity__Id}")
    @Operation(summary = "Get __entity__ by id", description = "Get __entity__ by id")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "__Entity__ found"),
            @ApiResponse(responseCode = "404", description = "__Entity__ not found")})
    public ResponseEntity<__Entity__Resource> get__Entity__ById(@PathVariable Long __entity__Id) {
        var get__Entity__ByIdQuery = new Get__Entity__ByIdQuery(__entity__Id);
        var __entity__ = __entity__QueryService.handle(get__Entity__ByIdQuery);
        if (__entity__.isEmpty()) return ResponseEntity.notFound().build();
        var __entity__Entity = __entity__.get();
        var __entity__Resource = __Entity__ResourceFromEntityAssembler.toResourceFromEntity(__entity__Entity);
        return ResponseEntity.ok(__entity__Resource);
    }

    /**
     * Get all __entities__
     *
     * @return The list of {@link __Entity__Resource} resources for all __entities__
     */
    @GetMapping
    @Operation(summary = "Get all __entities__", description = "Get all __entities__")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "__Entities__ found")})
    public ResponseEntity<List<__Entity__Resource>> getAll__Entities__() {
        var __entities__ = __entity__QueryService.handle(new GetAll__Entities__Query());
        var __entity__Resources = __entities__.stream()
                .map(__Entity__ResourceFromEntityAssembler::toResourceFromEntity)
                .toList();
        return ResponseEntity.ok(__entity__Resources);
    }

    /**
     * Update __entity__
     *
     * @param __entity__Id The __entity__ id
     * @param resource The {@link Update__Entity__Resource} instance
     * @return The {@link __Entity__Resource} resource for the updated __entity__
     */
    @PutMapping("/{__entity__Id}")
    @Operation(summary = "Update __entity__", description = "Update __entity__")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "__Entity__ updated"),
            @ApiResponse(responseCode = "400", description = "Invalid input"),
            @ApiResponse(responseCode = "404", description = "__Entity__ not found")})
    public ResponseEntity<__Entity__Resource> update__Entity__(@PathVariable Long __entity__Id, @RequestBody Update__Entity__Resource resource) {
        var update__Entity__Command = Update__Entity__CommandFromResourceAssembler.toCommandFromResource(__entity__Id, resource);
        var updated__Entity__ = __entity__CommandService.handle(update__Entity__Command);
        if (updated__Entity__.isEmpty()) return ResponseEntity.notFound().build();
        var updated__Entity__Entity = updated__Entity__.get();
        var updated__Entity__Resource = __Entity__ResourceFromEntityAssembler.toResourceFromEntity(updated__Entity__Entity);
        return ResponseEntity.ok(updated__Entity__Resource);
    }

    /**
     * Delete __entity__
     *
     * @param __entity__Id The __entity__ id
     * @return The message for the deleted __entity__
     */
    @DeleteMapping("/{__entity__Id}")
    @Operation(summary = "Delete __entity__", description = "Delete __entity__")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "__Entity__ deleted"),
            @ApiResponse(responseCode = "404", description = "__Entity__ not found")})
    public ResponseEntity<MessageResource> delete__Entity__(@PathVariable Long __entity__Id) {
        var delete__Entity__Command = new Delete__Entity__Command(__entity__Id);
        __entity__CommandService.handle(delete__Entity__Command);
        return ResponseEntity.ok(new MessageResource("__Entity__ with given id successfully deleted"));
    }
}
