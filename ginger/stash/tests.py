
from datetime import date

from django import test
from django.db import models
from django.contrib.auth.models import User

from . import utils


class RandomModel(models.Model):
    owner = models.ForeignKey(User)
    posted = models.DateTimeField()
    display_name = models.CharField(max_length=128)
    total_views = models.PositiveIntegerField(default=0)
        

class QueryFilterTest(test.SimpleTestCase):
    
    def query_filter(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', None)
        queryset = RandomModel.objects.filter(*args, **kwargs).all()
        if exclude:
            queryset = queryset.exclude(**exclude)
        func = utils.get_query_filter(queryset.query)
        return func
    
    def instance(self, **kwargs):
        ins = RandomModel()
        for k in kwargs:
            setattr(ins, k, kwargs[k])
        return ins
    
    def test_isnull(self):
        func = self.query_filter(posted__isnull=True)
        ins = self.instance(posted=1)
        self.assertFalse(func(ins))
        
        ins = self.instance(posted=None)
        self.assertTrue(func(ins))
        
    def test_missing_lookup(self):
        func = self.query_filter(owner__username="asdasd")
        self.assertIsNone(func)
        
    def test_iexact(self):
        ins = self.instance(display_name="Hello")        
        func = self.query_filter(display_name__iexact="hello")
        self.assertTrue(func(ins))
        
    def test_exact(self):
        func = self.query_filter(display_name="hello")
        ins = self.instance(display_name="Hello")
        self.assertFalse(func(ins))
        
        func = self.query_filter(total_views=9)
        ins = self.instance(total_views=8)
        self.assertFalse(func(ins))
        
        ins = self.instance(total_views=9)
        self.assertTrue(func(ins))
        
    def test_lt(self):
        func = self.query_filter(total_views__lt=9)
        ins = self.instance(total_views=2)
        self.assertTrue(func(ins))
        
        ins = self.instance(total_views=12)
        self.assertFalse(func(ins))
        
    def test_lte(self):
        func = self.query_filter(total_views__lte=9)
        ins = self.instance(total_views=9)
        self.assertTrue(func(ins))
                      
    def test_gt(self):
        func = self.query_filter(total_views__gt=9)
        ins = self.instance(total_views=12)
        self.assertTrue(func(ins))
        
        ins = self.instance(total_views=2)
        self.assertFalse(func(ins))

    def test_gte(self):
        func = self.query_filter(total_views__gte=9)
        ins = self.instance(total_views=9)
        self.assertTrue(func(ins))
        
    def test_multiple_operations(self):
        func = self.query_filter(display_name="hello", total_views=9)
        ins = self.instance(display_name="hello")
        self.assertFalse(func(ins))
        ins = self.instance(total_views=9)
        self.assertFalse(func(ins))
                
        ins = self.instance(display_name="hello", total_views=9)
        self.assertTrue(func(ins))
        
    def test_exclude(self):
        func = self.query_filter(display_name="hello", exclude={'total_views__lt':10})
        ins = self.instance(display_name="hello")
        self.assertFalse(func(ins))
        
        ins = self.instance(total_views=9)
        self.assertFalse(func(ins))
                
        ins = self.instance(display_name="hello", total_views=19)
        self.assertTrue(func(ins))
        ins = self.instance(display_name="hello", total_views=9)
        self.assertFalse(func(ins))   
        
        
class CacheKeyTest(test.SimpleTestCase):
    
    def test_args_key(self):
        value = utils.get_cache_key(1,2,3,4,dob=date.today())
        self.assertIsNotNone(value)
    
    def test_query_key(self):
        qs = RandomModel.objects.filter(owner__isnull=True).all()
        key = utils.get_cache_key_for_queryset(qs)
        self.assertIsNotNone(key)
        key2 = utils.get_cache_key_for_queryset(qs, op="count")
        self.assertNotEqual(key, key2)
        
                