pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        IMAGE_TAG = "kakao-game-ci:${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Build Image') {
            steps {
                sh 'docker build -t $IMAGE_TAG .'
            }
        }
        stage('Test') {
            steps {
                sh 'docker run --rm $IMAGE_TAG python -m pytest'
            }
        }
    }

    post {
        always {
            sh 'docker rmi -f $IMAGE_TAG || true'
        }
    }
}
