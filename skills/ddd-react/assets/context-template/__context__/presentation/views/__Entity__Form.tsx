import {useEffect, useState, type FormEvent} from 'react';
import {useNavigate, useParams} from 'react-router';
import {use__Context__Store} from '../../application/__context__.store';
import {__Entity__} from '../../domain/model/__entity-kebab__.entity';
import {__context__Paths} from '../__context__-paths';

/**
 * Routed view that creates or edits one __Entity__.
 *
 * One view serves both routes — the presence of an `id` parameter decides which. It
 * collects input, builds a domain object, and hands it to the store. The backend
 * validates again and stays the authority.
 */
export function __Entity__Form() {
    const navigate = useNavigate();
    const {id} = useParams();
    const isEdit = id !== undefined;

    const __entities__ = use__Context__Store(state => state.__entities__);
    const add__Entity__ = use__Context__Store(state => state.add__Entity__);
    const update__Entity__ = use__Context__Store(state => state.update__Entity__);

    const [name, setName] = useState('');

    useEffect(() => {
        if (!isEdit) return;
        // A route param is a string; compare against a number or nothing ever matches.
        const __entity__ = __entities__.find(candidate => candidate.id === Number(id));
        if (__entity__) setName(__entity__.name);
    }, [isEdit, id, __entities__]);

    function handleSubmit(event: FormEvent) {
        event.preventDefault();
        const __entity__ = new __Entity__({id: isEdit ? Number(id) : null, name});
        void (isEdit ? update__Entity__(__entity__) : add__Entity__(__entity__));
        navigate(__context__Paths.__entities__());
    }

    return (
        <section>
            <h1>{isEdit ? 'Edit __Entity__' : 'New __Entity__'}</h1>

            <form onSubmit={handleSubmit}>
                <label htmlFor="name">Name</label>
                <input id="name" required value={name} onChange={event => setName(event.target.value)}/>

                <button type="submit">{isEdit ? 'Update' : 'Create'}</button>
                <button type="button" onClick={() => navigate(__context__Paths.__entities__())}>Cancel</button>
            </form>
        </section>
    );
}
