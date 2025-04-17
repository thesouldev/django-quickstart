#!/bin/bash

GREEN="\033[0;32m"
CYAN="\033[0;36m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
BOLD="\033[1m"
RESET="\033[0m"

LOCAL_ENV_SECRET="team-utils-env-local"
PROD_ENV_SECRET="team-utils-env-prod"
CLOUD_RUN_SERVICE="asgard-web"

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${RESET}"
}


set_gcloud_project() {
    if [[ -z "$project" ]]; then
        print_message "${RED}" "Error: No project args provided. Please set the 'project' variable."
        return 1
    fi
    gcloud auth application-default set-quota-project "$project" > /dev/null 2>&1
    gcloud config set project "$project"
    print_message "${GREEN}" "GCloud Project: $project"
}


deploy_app() {
    if [[ -n "$(git status --porcelain)" ]]; then
        print_message "${RED}" "There are uncommitted changes in the repository. Please commit or stash them before deploying."
        exit 1
    fi

    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

    git fetch origin > /dev/null 2>&1
    git pull origin "$BRANCH_NAME" > /dev/null 2>&1

    LATEST_COMMIT=$(git rev-parse HEAD)
    LATEST_COMMIT_MSG=$(git log -1 --pretty=%B)

    USER_NAME=$(gcloud config get-value account 2> /dev/null)
    GCLOUD_PROJECT=$(gcloud config get-value project 2> /dev/null)

    if [[ -z "$GCLOUD_PROJECT" ]]; then
        print_message "${RED}" "No Google Cloud project is set. Please set the project using 'gcloud config set project <PROJECT_ID>'."
        exit 1
    fi

    echo -e "\n${BOLD}Build Summary:${RESET}\n"
    echo -e "Build Initiator:        ${USER_NAME}"
    echo -e "Branch:                 ${BRANCH_NAME}"
    echo -e "Commit:                 ${LATEST_COMMIT}"
    echo -e "Commit Message:         ${LATEST_COMMIT_MSG}"
    echo -e "Google Cloud Project:   ${GCLOUD_PROJECT}"

    echo ""
    print_message "${YELLOW}" "Do you want to proceed with the deployment? (y/n)"
    read -r proceed

    if [[ "$proceed" == "y" || "$proceed" == "Y" ]]; then
        print_message "${RESET}" "Deploying via Cloud Build..."

        gcloud build triggers run "$CLOUD_RUN_SERVICE" --branch="$BRANCH_NAME" --region="asia-south1" > /dev/null 2>&1
        
        if [[ $? -eq 0 ]]; then
            print_message "${GREEN}" "Build triggered successfully."
        else
            print_message "${RED}" "Failed to trigger the build."
            exit 1
        fi
    else
        print_message "${YELLOW}" "Deployment aborted."
        exit 0
    fi
}

update_env() {
    echo -e "${CYAN}${BOLD}Please select the environment you wish to update:${RESET}"
    echo -e "\t${YELLOW}1) ${GREEN}Local${RESET} ${BOLD}(.env.local)${RESET}"
    echo -e "\t${YELLOW}2) ${GREEN}Prod${RESET} ${BOLD}(.env.prod)${RESET}"

    read -p "$(echo -e ${CYAN}Enter your choice: ${RESET})" choice

    case $choice in
        1)
            gcloud secrets versions add "$LOCAL_ENV_SECRET" --data-file=.env.local
            gcloud secrets versions access latest --secret="$LOCAL_ENV_SECRET" --format='get(payload.data)' | tr -d '"' | base64 --decode > .env.local
            echo -e "${GREEN}.env.local file updated successfully.${RESET}"
            ;;
        2)
            gcloud secrets versions add "$PROD_ENV_SECRET" --data-file=.env.prod
            gcloud secrets versions access latest --secret="$PROD_ENV_SECRET" --format='get(payload.data)' | tr -d '"' | base64 --decode > .env.prod
            echo -e "${GREEN}.env.prod file updated successfully.${RESET}"
            ;;
        *)
            echo -e "${RED}Invalid choice. Please select either 1 or 2.${RESET}"
            exit 1
            ;;
    esac
}

set_env() {
    if [[ -z "$env" ]]; then
        print_message "${RED}" "Error: No env args provided. Please set the 'env' variable."
        return 1
    fi

    case "$env" in
        "local")
            gcloud secrets versions access latest --secret="$LOCAL_ENV_SECRET" --format='get(payload.data)' | tr -d '"' | base64 --decode > ../.env.local
            cp .env.local .env
            print_message "${GREEN}" "Environment updated for local"
            ;;
        "prod")
            gcloud secrets versions access latest --secret="$PROD_ENV_SECRET" --format='get(payload.data)' | tr -d '"' | base64 --decode > ../.env.prod
            cp .env.prod .env
            print_message "${GREEN}" "Environment updated for prod"
            ;;
        *)
            print_message "${RED}" "Invalid environment. Please specify 'local' or 'prod'."
            return 1
            ;;
    esac
}


# Main menu to execute the functions
case "$1" in
    set-gcloud-project) set_gcloud_project ;;
    deploy) deploy_app ;;
    update-env) update_env ;;
    set-env) set_env ;;
    *)
        print_message "${RED}" "Usage: $0 {set-gcloud-project|update-env}"
        exit 1
esac
