pipeline {
    agent none
    triggers { pollSCM('H/3 * * * *') }
    stages {
        stage ('Build') {
            agent any
            steps {
                sh 'pip install -U virtualenv'
                sh 'python -m virtualenv --clear env'
                sh './scripts/jenkins_build.sh'
                sh './scripts/jenkins_archive.sh'
            }
            post {
                always { deleteDir() }
            }
        } 
        stage ('Performance-Test') {
            agent { label 'perf-ubuntu-a0' }
            when { expression { return env.BRANCH_NAME == 'master' || env.BRANCH_NAME.startsWith('performance') } }
            steps {
                sh 'pip install -U virtualenv'
                sh 'python -m virtualenv --clear env'
                sh './scripts/jenkins_perf.sh'
            }
            post {
                always { deleteDir() }
            }
        }
    }
}
