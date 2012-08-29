#!/usr/bin/env python
import argparse
import commands
from ConfigParser import NoOptionError, NoSectionError
import getpass
import git
from github import Github
import os


class Engine(object):

    def __init__(self, debug=0, skip_auth=False):
        self.__debug = debug

        self._repo = self._get_repo()

        self._cw = self._repo.config_writer()
        self._cr = self._repo.config_reader()

        self._gh = None
        if not skip_auth:
            if self.__debug > 0:
                print "Authorizing engine..."
            self.do_auth()
            # Refresh the read-only reader.
            self._cr = self._repo.config_reader()

            self._gh_repo = self._gh.get_user().get_repo(self._cr.get('flowhub "structure"', 'name'))

    def do_auth(self):
        """Generates the authorization to do things with github."""
        try:
            token = self._cr.get('flowhub "auth"', 'token')
            self._gh = Github(token)
            if self.__debug > 0:
                print "GitHub Engine authorized by token in settings."
        except (NoSectionError, NoOptionError):
            if self.__debug > 0:
                print "No token - generating new one."

            print (
                "This appears to be the first time you've used Flowhub; "
                "we'll have to do a little bit of setup."
            )
            self._cw.add_section('flowhub "auth"')
            self._gh = Github(raw_input("Username: "), getpass.getpass())

            auth = self._gh.get_user().create_authorization(
                'public_repo',
                'Flowhub Client',
            )
            token = auth.token

            self._cw.set('flowhub "auth"', 'token', token)

            self._cw.add_section('flowhub "structure"')

            self._cw.set('flowhub "structure"', 'name',
                raw_input("Repository name for this flowhub: "))
            self._cw.set('flowhub "structure"', 'origin',
                raw_input("Name of your github remote? [origin] ") or 'origin')
            self._cw.set('flowhub "structure"', 'canon',
                raw_input('Name of the organization remote? [canon] ') or 'canon')

            self._cw.set('flowhub "structure"', 'master',
                raw_input("Name of the stable branch? [master] ") or 'master')
            self._cw.set('flowhub "structure"', 'develop',
                raw_input("Name of the development branch? [develop] ") or 'develop')

            self._cw.add_section('flowhub "prefix"')

            feature_prefix = raw_input("Prefix for feature branches [feature/]: ") or 'feature/'
            self._cw.set('flowhub "prefix"', 'feature', feature_prefix)
            release_prefix = raw_input("Prefix for releast branches [release/]: ") or "release/"
            self._cw.set('flowhub "prefix"', 'release', release_prefix)
            hotfix_prefix = raw_input("Prefix for hotfix branches [hotfix/]: ") or "hotfix/"
            self._cw.set('flowhub "prefix"', 'hotfix', hotfix_prefix)

            self.__write_conf()

            print (
                "You can change these settings just like all git settings, using the\n",
                "    git config\n",
                "command."
            )

            self._setup_repository_structure()

    def __write_conf(self):
        self._cw.write()

    def _setup_repository_structure(self):
        # make the repo...correct.
        pass

    def _get_repo(self):
        """Get the repository of this directory, or error out if not found"""
        repo_dir = commands.getoutput("git rev-parse --show-toplevel")
        if repo_dir.startswith('fatal'):
            raise RuntimeError("You don't appear to be in a git repository.")

        repo = git.Repo(repo_dir)
        return repo

    def publish_feature(self):
        repo = self._get_repo()
        gh = repo.remote(self._cr.get('flowhub "structure"', 'origin'))

    def create_release(self):
        # checkout develop
        # if already release branch, abort.
        # checkout -b relase_prefix+branch_name
        pass

    def create_hotfix(self):
        # Checkout master
        # if already hotfix branch, abort.
        # checkout -b hotfix_prefix+branch_name
        pass

    def apply_hotfix(self):
        # pull canon
        # checkout master
        # merge --no-ff hotfix
        # tag
        # checkout develop
        # merge --no-ff hotfix
        # push --tags canon
        # delete hotfix branches
        pass

    def create_feature(self, name=None, create_tracking_branch=True):
        if name is None:
            raise RuntimeError("Please provide a feature name.")

        if self.__debug > 0:
            print "Creating new feature branch..."
        # Checkout develop
        # checkout -b feature_prefix+branch_name
        # push -u origin feature_prefix+branch_name
        branch_name = "{}{}".format(self._cr.get('flowhub "prefix"', 'feature'), name)
        repo = self._get_repo()
        repo.create_head(
            branch_name,
            commit=repo.heads.develop,  # Requires a develop branch.
        )

        if create_tracking_branch:
            repo.git.push(self._cr.get('flowhub "structure"', 'origin'), branch_name, set_upstream=True)

        branch = [x for x in repo.branches if x.name == branch_name]
        # Checkout the branch.
        branch[0].checkout()

        print '\n'.join((
            "Summary of actions: ",
            "\tNew branch {} created, from branch {}".format(branch_name, self._cr.get('flowhub "structure"', 'develop')),
            "Switched to branch {}".format(branch_name),
        ))

    def prepare_release(self):
        pass

    def publish_release(self):
        # pull canon
        # checkout master
        # merge --no-ff release
        # tag
        # checkout develop
        # merge --no-ff release
        # push --tags canon
        # delete release branches
        pass

    def cleanup_branches(self):
        # hotfixes: remove from origin, local if match not found on canon
        # releases: remove from origin, local if match not found on canon
        # features: if pull request found and accepted, delete from local and origin
        pass


def handle_feature_call(args, engine):
    if args.verbosity > 1:
        print "handling feature"
    if args.action == 'start':
        engine.create_feature(
            name=args.name,
            create_tracking_branch=(not args.no_track),
        )

    elif args.action == 'switch':
        return

    elif args.action == 'publish':
        engine.publish_feature()

    else:
        raise RuntimeError("Unrecognized command for features: {}".format(args.action))


def handle_hotfix_call(args, engine):
    if args.verbosity > 1:
        print "handling hotfix"


def handle_release_call(args, engine):
    if args.verbosity > 1:
        print "handling release"


def handle_cleanup_call(args, engine):
    if args.verbosity > 1:
        print "handling cleanup"


if __name__ == "__main__":
    print "You are calling the core flowhub file as an executable."

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbosity', action="store", type=int, default=0)
    subparsers = parser.add_subparsers(dest="subparser")
    init = subparsers.add_parser('init',
        help="set up a repository to user flowhub",)
    feature = subparsers.add_parser('feature',
        help="do feature-related things",)
    hotfix = subparsers.add_parser('hotfix',
        help="do hotfix-related things",)
    release = subparsers.add_parser('release',
        help="do release-related things",)
    cleanup = subparsers.add_parser('cleanup',
        help="do repository-cleanup related things",)

    feature_subs = feature.add_subparsers(dest='action')
    fstart = feature_subs.add_parser('start',
        help="start a new feature branch")
    fstart.add_argument('name', help="name of the feature branch")
    fstart.add_argument('--no-track', default=False, action='store_true',
        help="do *not* set up a tracking branch on origin.")
    fswitch = feature_subs.add_parser('switch',
        help="switch to a different feature (by name)")
    fswitch.add_argument('name', help="name of feature to switch to")
    publish = feature_subs.add_parser('publish',
        help="send the current feature branch to origin and create a pull-request")

    hotfix_subs = hotfix.add_subparsers(dest='action')
    hstart = hotfix_subs.add_parser('start',
        help="start a new hotfix branch")
    apply = hotfix_subs.add_parser('apply',
        help="apply a hotfix branch to master and develop branches")

    release_subs = release.add_subparsers(dest='action')
    rstart = release_subs.add_parser('start',
        help="start a new release branch")
    rstart.add_argument('name', help="name of the release branch.")
    rprepare = release_subs.add_parser('prepare',
        help="send a release branch to a staging environment")
    rpublish = release_subs.add_parser('publish',
        help="merge a release branch into master and develop branches")

    cleanup_subs = cleanup.add_subparsers()

    args = parser.parse_args()
    if args.verbosity > 1:
        print "Args: ", args

    e = Engine(debug=args.verbosity)

    if args.subparser == 'feature':
        handle_feature_call(args, e)

    elif args.subparser == 'hotfix':
        handle_hotfix_call(args, e)

    elif args.subparser == 'release':
        handle_release_call(args, e)

    elif args.subparser == 'cleanup':
        handle_cleanup_call(args, e)

    else:
        raise RuntimeError("Whoa, unrecognized command: {}".format(args.subparser))