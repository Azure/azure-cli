node {
  stage ('Build') {
    node ('linux-build') {
      checkout scm
      sh './scripts/jenkins_build.sh'
      sh './scripts/jenkins_archive.sh'
      deleteDir()
    }
  } 
  stage ('Performance Test') {
    def platforms = ['perf-ubuntu-a0', 'perf-ubuntu-ds1']
    def perftests = [:]

    for (int i = 0; i < platforms.size(); i++) {
      platform = platforms.get(i)
      perftests["Test ${platform}"] = perf_closure(platform)
    }
    perftests.failFast = false

    parallel perftests
  }
}

def perf_closure(platform) {
  return {
    node (platform) {
      if (env.BRANCH_NAME != null && (env.BRANCH_NAME == 'master' || env.BRANCH_NAME.startsWith('performance'))) {
        checkout scm
        echo "Running performance test on ${platform}."
        sh './scripts/jenkins_perf.sh'
        deleteDir()
      }
      else {
        echo "Skip performance test."
      }
    }
  }
}