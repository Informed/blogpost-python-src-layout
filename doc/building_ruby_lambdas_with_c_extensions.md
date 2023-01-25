# Building AWS Ruby Lambdas that Require Gems with Native Extension

## What's the Problem?

If your Ruby development environment (e.g. a Mac) is different from your target Lambda in terms of operating system or architecture, there may be problems creating your Lambda image. This is especially true if your Ruby Gem Dependencies include C extensions. Without taking special steps, you may end up with a Lambda image that won't work when you try to run the Lambda.

This is due to the fact that some Gems have native extensions that ether have prebuilt versions for specific target OS and architectures. Many common Gems have native extentions. Some of these include Gems like `nokogiri`, `json`,  `nio4r` and `ffi`.

When you run `bundle install` on your Mac to create a `vendor/bundle` that you expect to package into your Lambda image, you will only get the versions of these GEMS that are for your Mac OS and architecture. For instance an M1 Mac will install native extention Gems for `arm64-darwin` 

If you zip that up into your Lambda function image and run it, you may see an error message similar to the following in your Cloudwatch logs when trying to run the Lambda (Gems that have Extensions will be listed in the `Could not  find` line):
```
"errorMessage": "Could not find byebug-11.1.3, json-2.6.2, nokogiri-1.14.0, racc-1.6.2 in any of the sources",
"errorType": "Init<Bundler::GemNotFound>",
```

Note that this situation would happen not just for Macs, but for any development environment that is not the same OS (Linux) and runtime architecture (arm64 or amd64/x86_64) as your target Lambda.

## Bundle in a Quick Lambda Linux Docker Container 

The solution, as usual in such cases, is to use Docker to do the Gem Bundling in an environment that is the same as your target Lambda. It would be nice to still do it as a series of shell commands or part of a script and not bother with needing a `Dockerfile`. Turns out its pretty easy:

```
dir=`pwd`
bundle config set --local deployment 'true'
docker run --platform=linux/amd64 \
  -e BUNDLE_SILENCE_ROOT_WARNING=1 \
  -v `pwd`:`pwd` \
  -w `pwd` \ 
  amazon/aws-sam-cli-build-image-ruby2.7 bundle install
bundle config unset deployment
bundle config unset path
```

That command effectively runs `bundle install` in your current directory, except it is being run in the context of an AWS Lambda amd64 (x86_64) Linux with all the build tools for Ruby.

This Docker runtime has the current directory of your Mac mapped into its current directory. So it can read and write any files and directories it needs from your project.

## Dissecting the Commands

Here's some more details on what each line of the command do:

1. `` dir=`pwd` ``
    Capture the current directory path in a shell variable just to make it easy to reuse in the following commands
1. `bundle config set --local deployment 'true'`
    Set `bundler` configuration to `deployment` mode
    1. `bundle install --deployment` [among other flags are depreciated](https://bundler.io/v2.4/man/bundle-install.1.html#OPTIONS) and its now recommended to use [bundle config](https://bundler.io/v2.4/man/bundle-config.1.html) to manage things like we do here.
        1. Either style of command updates the local `.bundle/config` in your project with
            ```
BUNDLE_DEPLOYMENT: "true"
BUNDLE_PATH: "vendor/bundle"
            ```  
        1. `--local` ensures that this gets applied only to your project
        1. `deployment  true`:
            * Disallows changes to the `Gemfile` if the `Gemfile.lock` is older than Gemfile
            * It also sets the `BUNDLE_PATH` to `vendor/bundle`
            * This config be "sticky" after this which you probably don't want if you later do normal local development 
                * Later `config unset` commands will unset these
1. `docker run`
    The start of the [docker command run](https://docs.docker.com/engine/reference/commandline/run/). The following are the arguments to this command
    1. `-e BUNDLE_SILENCE_ROOT_WARNING=1`
        * Suppress the warning not to run as root, as docker default to the root user
        * Processes in docker container run as `root` unless you do some work to add users and set it to run as another user. And `bundler` issues warnings if you run it as root. So the -e flag creates an Environment Variable `BUNDLE_SILENCE_ROOT_WARNING` that is consumed by `bundler` and tells `bundler` not to issue that warning. 
        *  This is not required, but those warnings are aestheticly unpleasing. 
    1. `-v ${dir}:${dir}`
        * Bind mount a volume: Maps the top of your ruby project with the Gemfile (`` `pwd` `` aka `${dir}` aka your current directory) into the docker container with the same path.
    1. `-w ${dir}`
        * Working directory inside the container: Sets the working directory of the docker container runtime to be same as our current directory path. 
        * This flag + the `-v` flag enables_the `bundler` process running in the container to read and write all the files and directories in your project.
    1. `amazon/aws-sam-cli-build-image-ruby2.7` 
        * Positional argument that specifies the docker image to use
        * We use the [amazon/aws-sam-cli-build-image-ruby2.7](https://hub.docker.com/r/amazon/aws-sam-cli-build-image-ruby2.7) image from DockerHub because its an image that has everything your ruby lambda Linux runtime will have plus it has all the Linux build tools needed to build any Ruby gems with extentions. 
        * You don't need to be using SAM to use this image. 
        * The same image is also available from AWS ECR as [public.ecr.aws/sam/build-ruby2.7](https://gallery.ecr.aws/sam/build-ruby2.7). 
        * It would be possible to use other images that have what you need, but this one seems to work well.
    1. `bundle install`
        * Positional last argument: The `bundle` command to run once the docker image starts.
        
1. `bundle config unset deployment`
    * This combined with the next command unsets what `bundle config set deployment true` set.
    * You will probably want to run these two commands before doing any `bundle` commands before doing any normal local development.
1. `bundle config unset path`
    * See previous command description

## Wrapping Things Up

If you use a modern Linux environment with the same processor architecture as your target Lambda, you can probably get away without having to use this Docker work around. Though it could still be safest to use this even there. The docker container being used is literally the same linux runtime as the target Lambda.

Otherwise, this technique should work for just about any development environment that can run Docker containers and run similar commands. Its only been tested it on a Mac though.

Do let me know if you have any feedback,  know of any better ways or have improvements to this technique in the comments or by contacting me directly.


