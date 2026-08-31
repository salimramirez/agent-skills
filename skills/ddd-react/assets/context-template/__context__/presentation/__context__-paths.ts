/**
 * Every URL the __context__ context owns, built in one place.
 *
 * React Router has no named routes, so a path typed into `navigate()` is a broken
 * link waiting for someone to rename a segment. These builders give the guarantee a
 * route name would: change a segment here and every caller follows.
 */
export const __context__Paths = {
    __entities__: () => '/__context__/__entities-kebab__',
    new__Entity__: () => '/__context__/__entities-kebab__/new',
    edit__Entity__: (id: number | string) => `/__context__/__entities-kebab__/${id}/edit`
} as const;
