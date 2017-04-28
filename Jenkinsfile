pipeline {
  agent none
  triggers { pollSCM('H/1 * * * *')}
  stages {
    stage ('Build') {
      agent { label 'linux-build' } 
      steps {
        checkout scm
        sh './scripts/jenkins_build.sh'
        sh './scripts/jenkins_archive.sh'
        deleteDir()
      }
      post {
        always { deleteDir() }
      }
    } 
    stage ('Test') {
      steps {
        script {
          def test_tasks = [:]

          // Add live test tasks
          def modules = ['acs', 'keyvault', 'storage', 'sql']
          for (int i = 0; i < modules.size(); ++i) {
            def name = modules.get(i)
            test_tasks["Live Test: ${name}"] = {
              node('linux-build') {
                checkout scm
                withCredentials([[$class: 'UsernamePasswordMultiBinding', 
                                  credentialsId: 'AzureSDKADGraph2',
                                  usernameVariable: 'AZURE_CLI_TEST_DEV_SP_NAME', 
                                  passwordVariable: 'AZURE_CLI_TEST_DEV_SP_PASSWORD']]) {
                withCredentials([string(credentialsId: 'AzureSDKADGraph2_Tenant',
                                        variable: 'AZURE_CLI_TEST_DEV_SP_TENANT')]) {
                  sh "./scripts/jenkins_live_test.sh ${name}"
                }}
              }
            }
          }

          // Add performance test tasks
          def platforms = ['perf-ubuntu-a0', 'perf-ubuntu-ds1']
          for (int i = 0; i < platforms.size(); i++) {
            platform = platforms.get(i)
            test_tasks["Performance Test: ${platform}"] = perf_closure(platform)
          }

          test_tasks.failFast = false
          parallel test_tasks
        }
      }
    }
  }
}

def perf_closure(platform) {
  return {
    node (platform) {
      if (env.BRANCH_NAME != null && (env.BRANCH_NAME == 'master' || env.BRANCH_NAME == 'jenkins' || env.BRANCH_NAME.startsWith('performance'))) {
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
