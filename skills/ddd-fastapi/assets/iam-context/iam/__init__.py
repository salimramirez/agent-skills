"""Identity and Access Management (IAM) bounded context.

Owns user accounts: sign-up, sign-in, and the bearer token every other
context's routes require. A user here is an *account*, not a person of the
domain: the people the domain talks about live in their own contexts, as
aggregates of their own, and refer to an account by its id.
"""
