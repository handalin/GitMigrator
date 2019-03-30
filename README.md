# GitMigrator
A simple git migrator using Python

After setting up your own Gogs server, you can migrate repositories using Gogs.

Though, Gogs migrate repos without issues(including milestones/labels/comments)

This simple migrator may help.


###now:
you can migrate your Github issues to your own Gogs server.

###future:
migrate Gogs issues back to Github.

## Usage

`git clone https://github.com/handalin/GitMigrator
cd GitMigrator
vi config.py`

### set up a new Github Personal Access Token

update config.py with your own settings then:

`./migrate_from_github_to_gogs.py`


## Implementation
1. Simple 'github client' (using github API)
2. Simple 'Gogs DAO' (operate the Gogs database directly)
3. a formator that do the dirty works ^_^.
