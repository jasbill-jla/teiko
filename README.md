# Teiko Technical

## Thank You

Thank you for this opportunity!  I genuinely enjoyed the opportunity to work on this technical evaluation.  Maybe that sounds weird.  I don't know, but I really do enjoy software development and math and science and the domain of this evaluation truly triggered my imagination.

## Claude Code

I used Claude Code throughout this evaluation.  I am unapologetic about that.  I think the use of AI code assistants/agents is undeniably the state of the software development world and so it makes sense to perform this evaluation in that mode.  To be clear, I did not simply feed the evaluation specification to Claude Code and sit back and wait for the result.  In spite of using Claude Code, this is still my work.  With the exception of "use Python and SQLite", I decided what technologies to use and how to use them (you decided on Python and SQLite).  I did lean on Claude Code to help me make those decisions and I leaned even heavier on Claude Code to actually write the code.  That is the purpose of an AI coding assistant.  In fact, I want to point out that I have only a modicum of experience with Python and none with React, but thanks to Claude Code, I was able to apply my understanding of Computer Science concepts and web application technology to this evaluation without being distracted by the nuances of a particular development environment.

## Running

You requested a Makefile in the root directory of the repo with specific targets and indicated that you would use the makefile and GitHub Codespaces to automatically grade my submission.  For that reason, that is exactly how you should run my code.  Create and start the codespace from my repo.  In the codespace terminal run:

1. make setup
2. make pipeline
3. make dashboard

Upon running make dashboard the codespace will proffer a button with which you can start your local browser and open my dashboard.  That button will eventually disappear on its own.  If you miss it, simply switch from the terminal tab to the ports tab and there you will find a link icon (looks like a globe) that you can use to launch my dashboard.

### load_data.py

The evaluation specification called for a Python script named load_data.py in the repo root that can be executed as "python load_data.py".  It also said the script should be executable directly without command-line arguments or module-style execution.  I wasn't completely sure what your goals were regarding "no module-style execution."  Did that mean you wanted load_data.py to not depend on any environment setup (other than core Python)?  Or did that just mean that you are going to run a script that includes the exact command "python load_data.py"?  Ultimately I decided you probably meant the latter and did not worry about making a version of load_data.py that did not rely on any environment setup.  I will explain this a little more in the Database section, below.

## Database Schema

I placed an ERD in the docs subdirectory.  This ERD is the result of my analysis of the dataset you provided.  While the ERD identifies five entities (Project, Subject, Condition, Treatment, and Sample), my database only has three tables (Project, Subject, and Sample).  The ERD includes Condition and Treatment as these are real entities that are referenced by the data in the dataset, but the analysis shows that the dataset only includes a name/id for each condition or treatment and so representing the Condition and/or Treatment entities in the database would lead to unnecessary complexity.  This is more a matter of query simplicity than it is a matter of performance, but the cost of development and maintenance should always be considered.  Should the need arise to store and use more information pertaining to conditions and/or treatments, it may be prudent to introduce tables for those two entities.

With the exception of the ID fields, the database schema is fully normalized which essentially means we are not storing any duplicate or derived data.  I called out the ID fields because they ARE essentially derived data.  For example, each project has its own ID (e.g. prj1), but I have chosen to store each project with an artificial, integer ID.  Doing this (1) ensures that record references throughout the system are consistent, (2) decouples internal referential integrity from the source data, and (3) helps performance with many, if not most relational database management systems (even if SQLite isn't really one of them).  Normalizing the data is more about data correctness than it is about performance, but in the case of this evaluation, with the information at my disposal, I have not identified any justification for de-normalizing the database schema.  The schema is very simple and should scale easily.  Any scaling risk due to dataset size is going to come from computations we need to perform on the data beyond querying for the data.

The evaluation's specification for the pipeline make target indicated some expectation that more must be done to set up the database (or other data sources) beyond simply loading the data from the CSV.  The very use of the word, "pipeline" seems to call for multiple steps.  My initial take on this was that I would load the data from the CSV and then I would perform some preprocessing on the data to support the desired dashboard functionality storing the results of the preprocessing in the database as well, perhaps with some schema separation to make it clear what is original data and what is derived from the original data.  In the end, I decided that I was not in possession of enough information to justify such preprocessing.  Allow me to explain.

### No Preprocessing

My setup includes alembic so that I could develop the database schema incrementally using migrations.  My expectation was, as I would work through the tasks of the evaluation I would learn more about the data and the processing that was necessary to satisfy the evaluation requirements and as I did so I would need to enhance the database schema.  As I worked through the evaluation tasks, however, I did not encounter anything that justified the type of preprocessing that I was anticipating.  In fact, the schema did not change from my initial setup (so, I didn't really make use of alembic).

#### Cell Population Frequencies

The computation of cell population frequencies was the first and most obvious choice for preprocessing and storing derived data.  Obviously, I could have stored the frequencies in the database to avoid computing them on demand when the dashboard rendered, but it seemed unnecessary.  The computation is a simple, inexpensive computation and the dataset would need to grow extremely large before the computation would become a legitimate performance concern.  In fact, the real performance concerns that I needed to address here was the transfer of the post-processed data from the backend to the browser (frontend) and the actual rendering of the data, which I handled by zipping the data for transit and adding paging to the data listing respectively.  Should I be given a much larger dataset and the frequency computation did become a performance issue I would rather turn to increasing computing resources or inexpensive code optimizations before turning to storing derived results.

#### Statistical Analysis

The statistical analysis of the cell population frequencies represented a couple more considerations for pre-processing.  First, the task called for the use of the data computed in the previous task (cell population frequencies).  Seemingly it would make sense to have stored cell population frequencies since I needed to use it again here, but again, it seemed an unnecessary complexity.  The frequencies are cheap to compute.  As long as I ensure that the recomputed results are exactly the same, then there is no reason to store the derived data.  Ensuring that the results are the same is a simple matter of code design and ensuring that the exact same code is used with the exact same inputs.  Storing derived data actually represents a bigger risk in the possibility of the original dataset drifting from what was used to compute the derived dataset.  Combating such drift is always a higher risk proposition than ensuring that the derivation is deterministic.

The second consideration was the statistical analysis itself.  While the evaluation specification called for the use of a specific subset of the sample data, it is a simple matter to parameterize the statistical analysis and make it useable with any subset of the sample data.  To handle this via pre-processing we would either have to know ahead of time which subsets of the data we were interested in or we would have to introduce a non-trivial, possibly expensive enhancement to the database schema and the code.  It is a reasonable argument that the statistical analysis could be expensive so that, as the dataset grows, the time to produce a result using a dynamic dashboard could become unacceptable, but I felt I was a long way from that in this exercise.  The analysis that I did apply was not a performance impediment with the given dataset.  Should I be given a much larger dataset and the analysis did become a performance issue I would rather turn to increasing computing resources or inexpensive code optimizations before turning to storing derived results.

#### Data Subset Analysis

For this task, I could have chosen to package up the specified subsets in some quickly transportable form, but that made no sense to me.  Relational databases are specifically designed for executing the types of queries called for by this task.  By creating a dynamic dashboard, Bob will be able to examine many sample subsets and counts, not just the ones specifically identified by this task.  The real risk with this task is the user requesting an improper subset (all of the samples).  Even with this small dataset, the "all" request is a little slow, but that is actually the cost to render the dataset and is not something that could be helped by pre-processing.

## Code Structure

The backend for the dashboard is a FastAPI implementation backed by two compute layers: pre-visualization and crunching.

The role of the crunching layer is to perform any computations on the raw source data that are needed to support the dashboard.  The crunching layer relies on SQLAlchemy to access the database.  SQLAlchemy was also used by load_data.py to populate the database so there is no risk of schema drift between the dashboard backend and load_data.py.  This is a major reason why I opted not to implement load_data.py without any external module dependencies.  The crunching layer encapsulates the code that would be needed to do any preprocessing should we decide that storing preprocessed data was a correct and necessary optimization in the future.

The role of the pre-visualization layer is to munge the data into a form that is convenient for the dashboard.  This layer decouples the database schema from the dashboard's requirements.

The frontend of the dashboard is a React implementation.  There are four API endpoints that are specifically designed to support the React frontend.  All API endpoint payloads are delivered as JSON.

The codebase includes regression tests.  The primary service provided by the regression tests in this case is to ensure that the code is doing what it is designed to do, but the real value in a production system would be to ensure that enhancements and fixes are not introducing unexpected issues.  A real beauty of AI assisted development is that it makes the development of these types of tests practical for systems that do not generate massive amounts of revenue.

### A Note About Statistical Significance

I waffled around a bit when working on Part 3, Statistical Analysis.  My initial feeling, being a software developer, was that the task was more about how I designed the implementation, but I eventually decided that the statement, "Statistics are needed to support any conclusion to convince Yah of Bob's findings." should be given more weight.  Initially I was simply determining statistical significance by direct comparison of the medians and I provided the dashboard user with the means to adjust the threshold for significance, but when I saw that the medians were varying by less than 1%, I decided that my approach might not be what you wanted.

Well, it has been a while since I have been immersed in statistics more complex than averages, medians, and standard deviations, so I consulted Claude.  Claude's suggestion, because we were already computing medians, was to apply a Mann-Whitney U analysis.  I challenged and iterated with Claude a bit on this, but eventually decided that my knowledge was too rusty and maybe too limited to really make an informed call on what the best analysis would be for the specified circumstances.  I decided to defer to Claude's judgement and own that.  So, the implementation of the Mann-Whitney U analysis is all Claude's work, but the organization of the code around it is my work.  Specifically I organized the code to allow for easy replacement of the Mann-Whitney U analysis with another analysis that can be similarly parameterized.

## Dashboard Link

I have not deployed the dashboard to a permanent cloud resource.  Therefore, I cannot supply a specific link to the dashboard.  Please refer to the Running section, above, for more information on accessing the dashboard.
