
from django.db import signals
from django.db.models import query
from django.db.models.query import QuerySet

from . import utils 



class FullyCachedQuerySet(QuerySet):
    
    def __init__(self, *args, **kw):
        super(FullyCachedQuerySet, self).__init__(*args, **kw)

    def flush_key(self):
        return flush_key(self.query_key())

    def iterator(self):
        iterator = super(FullyCachedQuerySet, self).iterator
        if self.timeout == NO_CACHE:
            return iter(iterator())
        else:
            try:
                # Work-around for Django #12717.
                query_string = self.query_key()
            except query.EmptyResultSet:
                return iterator()
            if FETCH_BY_ID:
                iterator = self.fetch_by_id
            return iter(CacheMachine(query_string, iterator, self.timeout, db=self.db))

    def fetch_by_id(self):
        """
        Run two queries to get objects: one for the ids, one for id__in=ids.

        After getting ids from the first query we can try cache.get_many to
        reuse objects we've already seen.  Then we fetch the remaining items
        from the db, and put those in the cache.  This prevents cache
        duplication.
        """
        # Include columns from extra since they could be used in the query's
        # order_by.
        vals = self.values_list('pk', *self.query.extra.keys())
        pks = [val[0] for val in vals]
        keys = dict((byid(self.model._cache_key(pk, self.db)), pk) for pk in pks)
        cached = dict((k, v) for k, v in cache.get_many(keys).items()
                      if v is not None)

        # Pick up the objects we missed.
        missed = [pk for key, pk in keys.items() if key not in cached]
        if missed:
            others = self.fetch_missed(missed)
            # Put the fetched objects back in cache.
            new = dict((byid(o), o) for o in others)
            cache.set_many(new)
        else:
            new = {}

        # Use pks to return the objects in the correct order.
        objects = dict((o.pk, o) for o in cached.values() + new.values())
        for pk in pks:
            yield objects[pk]

    def fetch_missed(self, pks):
        # Reuse the queryset but get a clean query.
        others = self.all()
        others.query.clear_limits()
        # Clear out the default ordering since we order based on the query.
        others = others.order_by().filter(pk__in=pks)
        if hasattr(others, 'no_cache'):
            others = others.no_cache()
        if self.query.select_related:
            others.query.select_related = self.query.select_related
        return others

    def count(self):
        super_count = super(FullyCachedQuerySet, self).count
        try:
            query_string = 'count:%s' % self.query_key()
        except query.EmptyResultSet:
            return 0
        if self.timeout == NO_CACHE or TIMEOUT == NO_CACHE:
            return super_count()
        else:
            return cached_with(self, super_count, query_string, TIMEOUT)


class FullyCachedManagerMixin(object):
    # Tell Django to use this manager when resolving foreign keys.
    use_for_related_fields = True
    
    def __init__(self, cache_name=None):
        super(FullyCachedManagerMixin, self).__init__()
    
    def get_cached_all(self):
        return 

    def get_queryset(self):
        return FullyCachedQuerySet(self.model, using=self._db)

    def contribute_to_class(self, cls, name):
        signals.post_save.connect(self.post_save, sender=cls)
        signals.post_delete.connect(self.post_delete, sender=cls)
        return super(FullyCachedManagerMixin, self).contribute_to_class(cls, name)

    def post_save(self, instance, **kwargs):
        self.invalidate(instance)

    def post_delete(self, instance, **kwargs):
        self.invalidate(instance)

    def invalidate(self, *objects):
        """Invalidate all the flush lists associated with ``objects``."""
        keys = [k for o in objects for k in o._cache_keys()]
        invalidator.invalidate_keys(keys)

    def raw(self, raw_query, params=None, *args, **kwargs):
        return CachingRawQuerySet(raw_query, self.model, params=params,
                                  using=self._db, *args, **kwargs)

  
    
    