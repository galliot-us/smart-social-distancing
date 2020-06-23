ATTENTION: *This folder is intended for internal DevOps only. This code is not being used by any module unless by installing and running `invoke`.* 

### CLI for development
Using docker for development requires repetitive commandline flags and arguments for building and running containers. 
This folder uses http://www.pyinvoke.org/ for generating common commandline commands. 

You don't have to use this tool. But it makes your life easier :)

### Usage
Independent of weather you run the containers on a remote server or on your own device, you need to have 
pyinvoke installed on your local development machine:

```bash
python3 -m pip install --user invoke
```

Once installed, you can use `invoke` (or its alias, `inv`) for invoking common commandline tasks. For getting a list of available tasks,
run the following command. You don't have to cd to the `tasks` dir. `invoke` looks for tasks in the working directory
or the parents of the working directory. Some tasks may require that you run them from the root repository directory:

```bash
inv --list
```

In order to invoke tasks, you should have `tasks/overrides.yaml` config file. For taking a look at available
configurable items and their default values, see `tasks/common/config.py`. You can start with editing this
template (don't forget to substitute `<YOUR_DOCKERHUB_USER_NAME>` with your dockerhub username in it):
```bash
cp tasks/overrides.yaml.template tasks/overrides.yaml
# now edit tasks/overrides.yaml. This file is in .gitignore 
```

Each task generates and runs a couple of commandline commands. The most common task is `develop.run`. In order to see what it does and read its documentation, run:

```bash
inv --help develop.run  
```

For example, if you want to run the app using x86-openvino.Dockerfile on your local machine (rather than remote), run:

```bash
inv -e develop.run --local
```

The `-e` flag in command above echos every command before running it. In order to preview commands, without actually 
running them, run it in dry-mode (using `-R`).

```bash
inv -R develop.run --local
```

Flags like `-e` (echo commands), `-R` (dry-mode), and `-h` (help) are generic flags, available for all tasks. 
But flags like `--local` in the command
above are task-specific. Task-specific flags MUST appear after the task name (e.g. `develop.run`) and the
generic flags must come before it. 


### Adding tasks
In order to add a task, create a function in `tasks/develop.py` or `tasks/release.py` and decorate it with
`@task`. The first argument to that function is usually named c (=context). The context is used for 
running bash commands (`c.run()`), temporarily changing directory (`with c.cd()`), reading configs(`c.config`), etc.
Rest of the arguments to that function become the command line arguments for that task.

In order to add another namespace besides `develop.py` or `release.py`, create another python module and register
it in `tasks/__init__.py`.  
