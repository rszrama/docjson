---
layout: default
title: DocJSON
---

DocJSON is a simple document format for building Hypermedia Web APIs.

A DocJSON document consists of standard JSON, with the addition of a set of hypermedia controls that are used to express the actions that may be taken.  DocJSON is a flexible document format and does not impose any structural restrictions either on the data representation style, or on the layout of hypermedia controls used within the document.

**Warning:** *The DocJSON specification is currently in draft, and is subject to change at any time.*

---

## Specification

A document may be any valid JSON, with the single restriction that the object key `"_type"` is reserved. An JSON object which contains a key named `"_type"` is considered a control object.

Any URLs within a document may be either relative or absolute.  Relative URLs should be resolved with respect to the original document URL.

The following control objects are currently supported:

### Link

A DocJSON link is a control element that represents a hyperlink that may be followed by the client.

* A link is any JSON object containing the `"_type"` key with a value of `"link"`.
* A link must have a key named `href`, which must contain a URL.

#### Example

{% highlight python %}
    {
        "_type": "link",
        "href": "http://todo.example.com/?completed=True"
    }
{% endhighlight %}

### Form

A DocJSON form is a control element that enables arbitrary actions to be taken by the client.  Forms specify the URL and HTTP method that should be used for the action, as well as the details of any parameters that should be included in the request.

* A link is any JSON object containing the `"_type"` key with a value of `"form"`.
* A form must have a key named `href`, which must contain a URL.
* A form must have a key named `method`, which must contain a valid HTTP method name.
* A form may have a key named `fields`.  If present, it must contain a list of objects.
* Any fields in the list must contain a key named `name`, which must contain a string.
* Any fields in the list may contain a key named `required`, which must contain a boolean.  If not present, the field should be treated as `"required": false`.
 
#### Example

{% highlight python %}
    {
        "_type": "form",
        "href": "http://todo.example.com/create_todo/",
        "method": "POST",
        "fields": [
            {"name": "text", "required": true},
            {"name": "completed"}
        ]
    }
{% endhighlight %}

### List

A DocJSON list is a paginated list of data.  The contents of the list may be any type of object, but the server does not have to populate the entire list, and can use pagination to serve further objects to the client on request.

* A link is any JSON object containing the `"_type"` key with a value of `"list"`.
* A list must have a key named `items`, which must contain a list.
* A list should have a key named `next`, which must contain URL, or `null`.
* The target of the `next` link should be a URL that returns a DocJSON List document.

#### Example

{% highlight python %}
    {
        "_type": "list",
        "items": [
            ...
        ]
        "next": "http://todo.example.com/items/?page=2"
    }
{% endhighlight %}

---

## Why another Hypermedia format?

None of the existing hypermedia formats meet the particular design goals of DocJSON.

* Collection+JSON presents a full range of hypermedia controls, but is specfic to representing list-like data structures.
* HAL presents link controls, but lacks other hypermedia controls.
* JSON API is specfic to data syncing between client and server, and does not present general purpose hypermedia controls.
* HTML is sometimes used or proposed for Hypermedia APIs, and offers hypermedia controls, but is a poor fit for data representations.

DocJSON is designed with the aim of making developers lives easier, by introducing a flexible data format with a sufficienty complete set of hypermedia controls.  By doing so we enable generic client libraries to be used to interact with DocJSON APIs, rather than rebuilding client libraries from scratch with each new API service.

---

## Example

The following is an example of a DocJSON document representing a simple ToDo API.

{% highlight python %}
    {
        "tabs": {
            "all": {"_type": "link", "href": "/"},
            "active": {"_type": "link", "href": "/?completed=False"},
            "completed": {"_type": "link", "href": "/?completed=True"}
        }
        "search": {
            "_type": "form",
            "method": "GET",
            "href": "/",
            "fields": [
                {"name": "text", "required": true}
            ]
        }
        "add_todo": {
            "_type": "form",
            "method": "POST",
            "href": "/",
            "fields": [
                {"name": "title", "required": true}
            ]
        }
        "items": {
            "_type": "list",
            "items": [
                {
                    "delete": {
                        "_type": "form",
                        "method": "DELETE",
                        "href": "/467/"
                    },
                    "edit": {
                        "_type": "form",
                        "method": "PUT",
                        "href": "/467/",
                        "fields": [{"name": "text"}, {"name": "completed"}]
                    },
                    "text": "Call mum",
                    "completed": false,
                    "created": "2013-10-16T19:20:30+01:00"
                },
                {
                    "delete": {
                        "_type": "form",
                        "method": "DELETE",
                        "href": "/466/"
                    },
                    "edit": {
                        "_type": "form",
                        "method": "PUT",
                        "href": "/466/",
                        "fields": [{"name": "text"}, {"name": "completed"}]
                    },
                    "text": "Fix the garage lock",
                    "completed": true,
                    "created": "2013-09-14T10:17:30+01:00"
                },
                ...
            ]
            "next": "/?page=2"
        }
{% endhighlight %}

The document presents the API client with the following controls:

* A set of tabs for switching between all notes, and complete or incomplete notes only.
* A search control for displaying notes that match a search string.
* A control for creating new todo notes.
* A paginated list of notes.
* Edit and delete controls for each note.

---

## Using a DocJSON client

Let's take a look at using a client library for DocJSON, to see what it can do.  There's currently a Python implementation.  Other languages are planned.

Create and activate a new virtual environment, install `docjson`, and start python. 

{% highlight python %}
    bash: virtualenv env
    bash: source env/bin/activate
    bash: pip install docjson
    bash: python
    >>> doc = docjson.get('http://docjson.heroku.com')
    >>> print doc.notes
    [
        {
            'text': 'Call mum',
            'completed': False,
            'delete': form(),
            'edit': form([text], [completed])
        },
        {
            'text': 'Fix the garage lock',
            'completed': False,
            'delete': form(),
            'edit': form([text], [completed])
        },
        ...
    ]
{% endhighlight %}

#### Pagination


The first thing to notice here is the ellipsis at the end of our notes list.  That indicates that there are more items in the paginated list that havn't yet been fetched.

If we iterate over the list or fetch an index that we don't yet have then the required pages will automatically be fetched for us.

{% highlight python %}
    >>> print doc.notes[6]
    {
        'text': 'File tax return',
        'completed': True,
        'delete': form(),
        'edit': form([text], [completed])
    }
{% endhighlight %}

#### Using forms

We can also add new notes...

{% highlight python %}
    >>> for idx in range(3):
    >>>     doc = doc.add_note(text='New note #%d' % idx)
{% endhighlight %}

Or edit an existing note...

{% highlight python %}
    >>> doc = doc.notes[2].edit(completed=True)
{% endhighlight %}

{% highlight python %}
    >>> doc = doc.notes[0].delete()
{% endhighlight %}

If we attempt to use a form with incorrect parameters, the client library will alert us.

{% highlight python %}
    >>> doc = doc.add_note()
    SDFSDFSSDGSDFE
{% endhighlight %}

{% highlight python %}
    >>> doc = doc.add_note(foobar='New note')
    DGDFGDFFD
{% endhighlight %}

#### Searching

As well as the 

{% highlight python %}
    >>> doc = doc.search(term='garage')
    >>> print doc.notes
    [
        {
            'text': 'Fix the garage lock',
            'completed': False,
            'delete': form(),
            'edit': form([text], [completed])
        }
    ]
{% endhighlight %}

#### Following links

{% highlight python %}
    >>> doc = doc.tabs.completed.get()
    >>> for note in doc.notes:
    >>>     print note.completed, note.text
{% endhighlight %}

{% highlight python %}
    >>> doc = doc.tabs.incomplete.get().search(term='garage')
    >>> print doc.notes
{% endhighlight %}

---

## Writing DocJSON services

DocJSON is of course language independant, and you should be able to develop DocJSON services in any decent server-side framework, such as Rails, Django or Node.

The example service used above is developed using Django REST framework, you can take a look here **TODO**


## Why you should be excited

The `docjson` client we've demonstrated doesn't have an prior knowledge about the server it's communicating with, and yet it's able to present the developer with a complete, ready-to-go library for interacting with the service.

It's simple, discoverable, and the client will always be instantly up to date with any server-side API changes.

DocJSON is appropriate for a very wide range of APIs, as it allows for flexible data representation, and supports a full range of hypermedia controls rather than just links or just CRUD-style interactions.

## The future, and what you can do to help

First up, feedback!

**TODO**

we need client libraries in various different languages etc.etc.


*Credits: Icon based on [document image][document-image] by [Gustavo Cordeiro][gustavo-cordeiro].*

[document-image]: http://thenounproject.com/noun/document/#icon-No19369
[gustavo-cordeiro]: http://thenounproject.com/gustavogcps/#
