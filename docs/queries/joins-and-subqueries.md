# Joins and subqueries

To join one table to another, so load also related models you can use following methods.

* `select_related(related: Union[List, str]) -> QuerySet`
* `prefetch_related(related: Union[List, str]) -> QuerySet`


* `Model`
    * `Model.load()` method


* `QuerysetProxy`
    * `QuerysetProxy.select_related(related: Union[List, str])` method
    * `QuerysetProxy.prefetch_related(related: Union[List, str])` method

## select_related

`select_related(related: Union[List, str]) -> QuerySet`

Allows to prefetch related models during the same query.

**With `select_related` always only one query is run against the database**, meaning
that one (sometimes complicated) join is generated and later nested models are processed in
python.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

!!!note 
    If you are coming from `django` note that `ormar` `select_related` differs ->
    in `django` you can `select_related`
    only singe relation types, while in `ormar` you can select related across `ForeignKey`
    relation, reverse side of `ForeignKey` (so virtual auto generated keys) and `ManyToMany`
    fields (so all relations as of current version).

!!!tip 
    To control which model fields to select use `fields()`
    and `exclude_fields()` `QuerySet` methods.

!!!tip 
    To control order of models (both main or nested) use `order_by()` method.

```python
class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)

class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: int = ormar.Integer(nullable=True)
```

```python
album = await Album.objects.select_related("tracks").all()
# will return album will all columns tracks
```

You can provide a string or a list of strings

```python
class SchoolClass(ormar.Model):
    class Meta:
        tablename = "schoolclasses"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    department: Optional[Department] = ormar.ForeignKey(Department, nullable=False)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    class Meta:
        tablename = "students"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(SchoolClass)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


class Teacher(ormar.Model):
    class Meta:
        tablename = "teachers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(SchoolClass)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)
```

```python
classes = await SchoolClass.objects.select_related(
    ["teachers__category", "students"]).all()
# will return classes with teachers and teachers categories
# as well as classes students
```

Exactly the same behavior is for Many2Many fields, where you put the names of Many2Many
fields and the final `Models` are fetched for you.

!!!warning 
    If you set `ForeignKey` field as not nullable (so required) during all
    queries the not nullable `Models` will be auto prefetched, even if you do not include
    them in select_related.

!!!note 
    All methods that do not return the rows explicitly returns a QueySet instance so
    you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

## prefetch_related

`prefetch_related(related: Union[List, str]) -> QuerySet`

Allows to prefetch related models during query - but opposite to `select_related` each
subsequent model is fetched in a separate database query.

**With `prefetch_related` always one query per Model is run against the database**,
meaning that you will have multiple queries executed one after another.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

!!!tip 
    To control which model fields to select use `fields()`
    and `exclude_fields()` `QuerySet` methods.

!!!tip 
    To control order of models (both main or nested) use `order_by()` method.

```python
class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)

class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: int = ormar.Integer(nullable=True)
```

```python
album = await Album.objects.prefetch_related("tracks").all()
# will return album will all columns tracks
```

You can provide a string, or a list of strings

```python
class SchoolClass(ormar.Model):
    class Meta:
        tablename = "schoolclasses"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    department: Optional[Department] = ormar.ForeignKey(Department, nullable=False)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    class Meta:
        tablename = "students"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(SchoolClass)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


class Teacher(ormar.Model):
    class Meta:
        tablename = "teachers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    schoolclass: Optional[SchoolClass] = ormar.ForeignKey(SchoolClass)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)
```

```python
classes = await SchoolClass.objects.prefetch_related(
    ["teachers__category", "students"]).all()
# will return classes with teachers and teachers categories
# as well as classes students
```

Exactly the same behavior is for Many2Many fields, where you put the names of Many2Many
fields and the final `Models` are fetched for you.

!!!warning 
    If you set `ForeignKey` field as not nullable (so required) during all
    queries the not nullable `Models` will be auto prefetched, even if you do not include
    them in select_related.

!!!note 
    All methods that do not return the rows explicitly returns a QueySet instance so
    you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

## select_related vs prefetch_related

Which should you use -> `select_related` or `prefetch_related`?

Well, it really depends on your data. The best answer is try yourself and see which one
performs faster/better in your system constraints.

What to keep in mind:

### Performance

**Number of queries**:
`select_related` always executes one query against the database,
while `prefetch_related` executes multiple queries. Usually the query (I/O) operation is
the slowest one but it does not have to be.

**Number of rows**:
Imagine that you have 10 000 object in one table A and each of those objects have 3
children in table B, and subsequently each object in table B has 2 children in table C.
Something like this:

```
                     Model C
                   /
           Model B - Model C
         / 
Model A  - Model B - Model C
       \           \ 
        \            Model C
         \
           Model B - Model C
                   \ 
                     Model C
```

That means that `select_related` will always return 60 000 rows (10 000 * 3 * 2) later
compacted to 10 000 models.

How many rows will return `prefetch_related`?

Well, that depends, if each of models B and C is unique it will return 10 000 rows in
first query, 30 000 rows
(each of 3 children of A in table B are unique) in second query and 60 000 rows (each of
2 children of model B in table C are unique) in 3rd query.

In this case `select_related` seems like a better choice, not only it will run one query
comparing to 3 of
`prefetch_related` but will also return 60 000 rows comparing to 100 000
of `prefetch_related` (10+30+60k).

But what if each Model A has exactly the same 3 models B and each models C has exactly
same models C? `select_related`
will still return 60 000 rows, while `prefetch_related` will return 10 000 for model A,
3 rows for model B and 2 rows for Model C. So in total 10 006 rows. Now depending on the
structure of models (i.e. if it has long Text() fields etc.) `prefetch_related`
might be faster despite it needs to perform three separate queries instead of one.

#### Memory

`ormar` is a mini ORM meaning that it does not keep a registry of already loaded models.

That means that in `select_related` example above you will always have 10 000 Models A,
30 000 Models B
(even if the unique number of rows in db is 3 - processing of `select_related` spawns **
new** child models for each parent model). And 60 000 Models C.

If the same Model B is shared by rows 1, 10, 100 etc. and you update one of those, the
rest of rows that share the same child will **not** be updated on the spot. If you
persist your changes into the database the change **will be available only after reload
(either each child separately or the whole query again)**. That means
that `select_related` will use more memory as each child is instantiated as a new object
- obviously using it's own space.

!!!note 
    This might change in future versions if we decide to introduce caching.

!!!warning 
    By default all children (or event the same models loaded 2+ times) are
    completely independent, distinct python objects, despite that they represent the same
    row in db.

    They will evaluate to True when compared, so in example above: 
    
    ```python
    # will return True if child1 of both rows is the same child db row 
    row1.child1 == row100.child1
    
    # same here:
    model1 = await Model.get(pk=1)
    model2 = await Model.get(pk=1) # same pk = same row in db
    # will return `True`
    model1 == model2
    ``` 
    
    but 
    
    ```python
    # will return False (note that id is a python `builtin` function not ormar one).
    id(row1.child1) == (ro100.child1)
    
    # from above - will also return False
    id(model1) == id(model2)
    ``` 

On the contrary - with `prefetch_related` each unique distinct child model is
instantiated only once and the same child models is shared across all parent models.
That means that in `prefetch_related` example above if there are 3 distinct models in
table B and 2 in table C, there will be only 5 children nested models shared between all
model A instances. That also means that if you update any attribute it will be updated
on all parents as they share the same child object.


## Model methods

Each model instance have a set of methods to `save`, `update` or `load` itself.

### load

You can load the `ForeignKey` related model by calling `load()` method.

`load()` can be used to refresh the model from the database (if it was changed by some other process).

!!!tip
    Read more about `load()` method in [models methods](../models/methods.md#load)

## QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey`
returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create,
select related etc related models directly from parent model.

### select_related

Works exactly the same as [select_related](./#select_related) function above but allows you to fetch related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

### prefetch_related

Works exactly the same as [prefetch_related](./#prefetch_related) function above but allows you to fetch related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


[querysetproxy]: ../relations/queryset-proxy.md