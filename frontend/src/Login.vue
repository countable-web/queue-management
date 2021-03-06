/*Copyright 2015 Province of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.*/


<template>
  <b-col id="login-form">
    <div v-show="!this.$store.state.isLoggedIn">
      <b-button @click="login()"
                id="login-button"
                style="padding-top: 10px"
                class="btn btn-primary">Login</b-button>
    </div>

    <div v-show="this.$store.state.isLoggedIn"
         style="display: flex; flex-direction: row; justify-content: space-between">
      <div id="select-wrapper" style="padding-right: 20px" v-if="reception">
         <select id="counter-selection" class="custom-select" v-model="counter_selection">
           <option value='counter'>Counter</option>
           <option value='quick'>Quick Trans</option>
           <option value='receptionist'>Receptionist</option>
        </select>
      </div>
      <div style="padding-right: 20px">
        <label class="navbar-label navbar-user">User: {{ this.$store.state.user.username }}</label>
        <label class="navbar-label">Office: {{ this.$store.state.user.office.office_name }}</label>
      </div>
      <div style="padding-top: 5px">
        <b-button v-show="this.$store.state.isLoggedIn"
                  @click="logout()"
                  id="logout-button"
                  class="btn btn-primary">Logout</b-button>
      </div>
    </div>
  </b-col>
</template>

<script>
import _ from 'lodash'
import { mapActions, mapGetters, mapMutations } from 'vuex'

  export default {
    name: 'Login',
    created() {
      this.setupKeycloakCallbacks()
      _.defer(this.initLocalStorage)
    },
    computed: {
      ...mapGetters(['quick_trans_status', 'reception', 'receptionist_status']),
      // set and get state of counter type (select dropdown in nav)
      counter_selection: {
        get() {
          if (this.quick_trans_status === true) {
            return 'quick';
          } else if (this.receptionist_status === true) {
            return 'receptionist';
          } else {
            return 'counter';
          }
        },
        set(value) {
          this.setQuickTransactionState(value === 'quick')
          this.setReceptionistState(value === 'receptionist')
          this.updateCSRState()
        }
      }
    },
    methods: {
      ...mapActions(['updateCSRState']),
      ...mapMutations(['setQuickTransactionState', 'setReceptionistState']),
      initLocalStorage() {
        if(localStorage.token) {
          let tokenExp = localStorage.tokenExp
          let timeUntilExp = Math.round(tokenExp - new Date().getTime() / 1000)
          if (timeUntilExp > 30) {
            this.$keycloak.init({
                responseMode: 'fragment',
                flow: 'standard',
                refreshToken: localStorage.refreshToken,
                token: localStorage.token,
                tokenExp: localStorage.tokenExp
            })
            .success( () => {

              //Set a timer to auto-refresh the token
              setInterval(() => { this.refreshToken(300); }, 60*1000)
              this.setTokenToLocalStorage()
              this.$store.commit('setBearer', localStorage.token)
            })
            .error( () => {
              this.init()
            })
          } else {
            this.init()
          }
        } else if (!localStorage.token) {
          this.init()
        }
      },

      init() {
        this.$keycloak.init({
            responseMode: 'fragment',
            flow: 'standard'
          }
        ).success( () => {
          setInterval(() => { this.refreshToken(300); }, 60*1000)
        })
      },

      setupKeycloakCallbacks(authenticated) {

        this.$keycloak.onAuthSuccess = () => {
          this.$store.dispatch('logIn', this.$keycloak.token)
          this.setTokenToLocalStorage()
          this.$root.$emit('socketConnect')
        }

        this.$keycloak.onAuthLogout = () => {
          this.$root.$emit('socketDisconnect')
          this.$store.commit('setBearer', null)
          this.$store.commit('logOut')
        }

        this.$keycloak.onAuthRefreshSuccess = () => {
          this.setTokenToLocalStorage()
          this.$store.commit('setBearer', this.$keycloak.token)
        }
      },

      setTokenToLocalStorage() {
        let tokenParsed = this.$keycloak.tokenParsed
        let token = this.$keycloak.token
        let refreshToken = this.$keycloak.refreshToken
        let tokenExpiry = tokenParsed.exp

        if (localStorage.token) {
          localStorage.removeItem("token")
          localStorage.removeItem("tokenExp")
          localStorage.removeItem("refreshToken")
        }
        localStorage.setItem("token", token)
        document.cookie = "oidc-jwt=" + this.$keycloak.token
        localStorage.setItem("tokenExp", tokenExpiry)
        localStorage.setItem("refreshToken", refreshToken)
      },

      login() {
        this.$keycloak.login({idpHint: 'idir'})
      },

      logout() {
        this.$keycloak.logout()
        localStorage.removeItem("token")
        localStorage.removeItem("tokenExp")
        localStorage.removeItem("refreshToken")
      },

      refreshToken(minValidity) {
        this.$keycloak.updateToken(minValidity).success(refreshed => {
          if (refreshed) {
            console.log(this.$keycloak.tokenParsed)
          } else {
            console.log('Token not refreshed, valid for ' + Math.round(this.$keycloak.tokenParsed.exp + this.$keycloak.timeSkew - new Date().getTime() / 1000) + ' seconds')
          }
        }).error( () => {
          output('Failed to refresh token')
        })
      },

      updateTransactionStatus(e) {
        this.setQuickTransactionState(e)
        this.updateCSRState()
      }
    }
  }
</script>

<style>
.custom-control-label::after, .custom-control-label::before {
  top: 3px;
}

.navbar-label {
  color: white;
  margin-bottom: 0px;
  float: left;
  clear: both;
}

.navbar-brand {
  font-size: .85rem;
}
</style>
