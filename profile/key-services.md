# Key Services

### Overview

![A diagram showing the major services in wellcomecollection.org](https://raw.githubusercontent.com/wellcomecollection/.github/main/profile/services.png)

* The Wellcome Collection website is the public face of our digital offering, and it pulls in content from a variety of services. (repo: [wellcomecollection.org](https://github.com/wellcomecollection/wellcomecollection.org)).
* Our account services allow users to manage [their library membership](https://wellcomecollection.org/pages/X\_2eexEAACQAZLBi), and will allow them to order items from the library's closed stores (pending release).
* Our editorial content – including stories, exhibitions, and events – is stored and managed [in Prismic](https://prismic.io/). We use the Prismic API to fetch content and display it on the site.
* The catalogue API powers our unified collections search. It's backed by a pipeline that combines data from different library and archive catalogues. (repos: [catalogue-api](https://github.com/wellcomecollection/catalogue-api), [catalogue-pipeline](https://github.com/wellcomecollection/catalogue-pipeline))
* Our storage service is the long-term preservation repository for our digital collections. It keeps our files in cloud storage providers, stores multiple copies for redundancy, and verifies every copy is stored correctly. (repo: [storage-service](https://github.com/wellcomecollection/storage-service))
* We have workflow systems that process new content before it's uploaded to the storage service. Currently we use [intranda's Goobi](https://www.intranda.com/en/digiverso/goobi/goobi-overview/) for digitised content and [Artefactual's Archivematica](https://www.archivematica.org/en/) for born-digital content. (repos: [goobi-infrastructure](https://github.com/wellcomecollection/goobi-infrastructure), [archivematica-infrastructure](https://github.com/wellcomecollection/archivematica-infrastructure))
* We make images available through [IIIF APIs](https://iiif.io/api/), an open standard used by many libraries and museums. Our IIIF services are provided by [Digirati](https://digirati.com/), and fetch images from the storage service. This includes both the APIs and the pre-processing required to make images available.