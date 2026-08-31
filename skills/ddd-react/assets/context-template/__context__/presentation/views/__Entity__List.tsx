import {useEffect} from 'react';
import {useNavigate} from 'react-router';
import {use__Context__Store} from '../../application/__context__.store';
import {__context__Paths} from '../__context__-paths';

/**
 * Routed view listing the __entities__ of the __context__ context.
 *
 * A view is the smart component: it selects from the store, dispatches actions and
 * navigates. It holds no business rule and makes no HTTP call.
 *
 * Each `use__Context__Store(state => …)` call selects one slice, so the component
 * re-renders only when that slice changes. Selecting the whole store re-renders on
 * every unrelated change.
 */
export function __Entity__List() {
    const navigate = useNavigate();
    const __entities__ = use__Context__Store(state => state.__entities__);
    const errors = use__Context__Store(state => state.errors);
    const __entities__Loaded = use__Context__Store(state => state.__entities__Loaded);
    const fetch__Entities__ = use__Context__Store(state => state.fetch__Entities__);
    const delete__Entity__ = use__Context__Store(state => state.delete__Entity__);

    useEffect(() => {
        if (!__entities__Loaded) void fetch__Entities__();
    }, [__entities__Loaded, fetch__Entities__]);

    return (
        <section>
            <h1>__Entities__</h1>

            {!__entities__Loaded && <p>Loading…</p>}
            {errors.length > 0 && <p role="alert">{errors.map(error => error.message).join(', ')}</p>}

            <ul>
                {__entities__.map(__entity__ => (
                    <li key={__entity__.id}>
                        <span>{__entity__.name}</span>
                        <button type="button" onClick={() => navigate(__context__Paths.edit__Entity__(__entity__.id!))}>
                            Edit
                        </button>
                        <button type="button" onClick={() => void delete__Entity__(__entity__.id!)}>
                            Delete
                        </button>
                    </li>
                ))}
            </ul>

            <button type="button" onClick={() => navigate(__context__Paths.new__Entity__())}>
                New __Entity__
            </button>
        </section>
    );
}
