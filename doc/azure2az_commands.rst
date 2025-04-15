
Azure classic CLI to Azure CLI commands
=========================================
Below is a list of common Azure classic CLI commands and their Azure CLI equivalent.

Services included:

* Account
* Network
* Storage
* VM

==========================================================   ==========================================================
Azure classic CLI                                            Azure CLI
==========================================================   ==========================================================
azure account clear                                          az account clear
azure account list                                           az account list
azure account set                                            az account set
azure account show                                           az account show
azure location list                                          az account list-locations
azure network application-gateway address-pool create        az network application-gateway address-pool create
azure network application-gateway address-pool delete        az network application-gateway address-pool delete
azure network application-gateway create                     az network application-gateway create
azure network application-gateway delete                     az network application-gateway delete
azure network application-gateway frontend-ip create         az network application-gateway frontend-ip create
azure network application-gateway frontend-ip delete         az network application-gateway frontend-ip delete
azure network application-gateway frontend-port create       az network application-gateway frontend-port create
azure network application-gateway frontend-port delete       az network application-gateway frontend-port delete
azure network application-gateway http-listener create       az network application-gateway http-listener create
azure network application-gateway http-listener delete       az network application-gateway http-listener delete
azure network application-gateway http-settings create       az network application-gateway http-settings create
azure network application-gateway http-settings delete       az network application-gateway http-settings delete
azure network application-gateway list                       az network application-gateway list
azure network application-gateway probe create               az network application-gateway probe create
azure network application-gateway probe delete               az network application-gateway probe delete
azure network application-gateway rule create                az network application-gateway rule create
azure network application-gateway rule delete                az network application-gateway rule delete
azure network application-gateway set                        az network application-gateway update
azure network application-gateway show                       az network application-gateway show
azure network application-gateway ssl-cert create            az network application-gateway ssl-cert create
azure network application-gateway ssl-cert delete            az network application-gateway ssl-cert delete
azure network application-gateway start                      az network application-gateway start
azure network application-gateway stop                       az network application-gateway stop
azure network application-gateway url-path-map create        az network application-gateway url-path-map create
azure network application-gateway url-path-map delete        az network application-gateway url-path-map delete
azure network application-gateway url-path-map rule create   az network application-gateway url-path-map rule create
azure network application-gateway url-path-map rule delete   az network application-gateway url-path-map rule delete
azure network dns record-set add-record                      az network dns record-set [ptr|mx|*] add
azure network dns record-set create                          az network dns record-set create
azure network dns record-set delete                          az network dns record-set delete
azure network dns record-set delete-record                   az network dns record-set [ptr|mx|*] remove
azure network dns record-set set                             az network dns record-set update
azure network dns record-set show                            az network dns record-set show
azure network dns zone create                                az network dns zone create
azure network dns zone delete                                az network dns zone delete
azure network dns zone list                                  az network dns zone list
azure network dns zone set                                   az network dns zone update
azure network dns zone show                                  az network dns zone show
azure network express-route authorization create             az network express-route circuit-auth create
azure network express-route authorization delete             az network express-route circuit-auth delete
azure network express-route authorization list               az network express-route circuit-auth list
azure network express-route authorization set                az network express-route circuit-auth update
azure network express-route authorization show               az network express-route circuit-auth show
azure network express-route circuit create                   az network express-route circuit create
azure network express-route circuit delete                   az network express-route circuit delete
azure network express-route circuit list                     az network express-route circuit list
azure network express-route circuit set                      az network express-route circuit update
azure network express-route circuit show                     az network express-route circuit show
azure network express-route peering create                   az network express-route circuit-peering create
azure network express-route peering delete                   az network express-route circuit-peering delete
azure network express-route peering list                     az network express-route circuit-peering list
azure network express-route peering set                      az network express-route circuit-peering update
azure network express-route peering show                     az network express-route circuit-peering show
azure network express-route provider list                    az network express-route service-provider list
azure network lb address-pool create                         az network lb address-pool create
azure network lb address-pool delete                         az network lb address-pool delete
azure network lb address-pool list                           az network lb address-pool list
azure network lb create                                      az network lb create
azure network lb delete                                      az network lb delete
azure network lb frontend-ip create                          az network lb frontend-ip create
azure network lb frontend-ip delete                          az network lb frontend-ip delete
azure network lb frontend-ip list                            az network lb frontend-ip list
azure network lb frontend-ip set                             az network lb frontend-ip update
azure network lb inbound-nap-pool delete                     az network lb inbound-nap-pool delete
azure network lb inbound-nat-pool create                     az network lb inbound-nat-pool create
azure network lb inbound-nat-pool list                       az network lb inbound-nat-pool list
azure network lb inbound-nat-pool set                        az network lb inbound-nat-pool update
azure network lb inbound-nat-rule create                     az network lb inbound-nat-rule create
azure network lb inbound-nat-rule delete                     az network lb inbound-nat-rule delete
azure network lb inbound-nat-rule list                       az network lb inbound-nat-rule list
azure network lb inbound-nat-rule set                        az network lb inbound-nat-rule update
azure network lb list                                        az network lb list
azure network lb probe create                                az network lb probe create
azure network lb probe delete                                az network lb probe delete
azure network lb probe list                                  az network lb probe list
azure network lb probe set                                   az network lb probe update
azure network lb rule create                                 az network lb rule create
azure network lb rule delete                                 az network lb rule delete
azure network lb rule list                                   az network lb rule list
azure network lb rule set                                    az network lb rule update
azure network lb set                                         az network lb update
azure network lb show                                        az network lb show
azure network local-gateway create                           az network local-gateway create
azure network local-gateway delete                           az network local-gateway delete
azure network local-gateway list                             az network local-gateway list
azure network local-gateway set                              az network local-gateway update
azure network local-gateway show                             az network local-gateway show
azure network nic create                                     az network nic create
azure network nic delete                                     az network nic delete
azure network nic ip-config address-pool create              az network nic ip-config address-pool add
azure network nic ip-config address-pool delete              az network nic ip-config address-pool remove
azure network nic ip-config create                           az network nic ip-config create
azure network nic ip-config delete                           az network nic ip-config delete
azure network nic ip-config inbound-nat-rule create          az network nic ip-config inbound-nat-rule add
azure network nic ip-config inbound-nat-rule delete          az network nic ip-config inbound-nat-rule remove
azure network nic ip-config list                             az network nic ip-config list
azure network nic ip-config set                              az network nic ip-config update
azure network nic ip-config show                             az network nic ip-config show
azure network nic list                                       az network nic list
azure network nic set                                        az network nic update
azure network nic show                                       az network nic show
azure network nsg create                                     az network nsg create
azure network nsg delete                                     az network nsg delete
azure network nsg list                                       az network nsg list
azure network nsg rule create                                az network nsg rule create
azure network nsg rule delete                                az network nsg rule delete
azure network nsg rule list                                  az network nsg rule list
azure network nsg rule set                                   az network nsg rule update
azure network nsg rule show                                  az network nsg rule show
azure network nsg set                                        az network nsg update
azure network nsg show                                       az network nsg show
azure network public-ip create                               az network public-ip create
azure network public-ip delete                               az network public-ip delete
azure network public-ip list                                 az network public-ip list
azure network public-ip set                                  az network public-ip update
azure network public-ip show                                 az network public-ip show
azure network route-table create                             az network route-table create
azure network route-table delete                             az network route-table delete
azure network route-table list                               az network route-table list
azure network route-table route create                       az network route-table route create
azure network route-table route delete                       az network route-table route delete
azure network route-table route list                         az network route-table route list
azure network route-table route set                          az network route-table route update
azure network route-table route show                         az network route-table route show
azure network route-table set                                az network route-table update
azure network route-table show                               az network route-table show
azure network traffic-manager endpoint create                az network traffic-manager endpoint create
azure network traffic-manager endpoint delete                az network traffic-manager endpoint delete
azure network traffic-manager endpoint set                   az network traffic-manager endpoint update
azure network traffic-manager endpoint show                  az network traffic-manager endpoint show
azure network traffic-manager profile create                 az network traffic-manager profile create
azure network traffic-manager profile delete                 az network traffic-manager profile delete
azure network traffic-manager profile is-dns-available       az network traffic-manager profile check-dns
azure network traffic-manager profile list                   az network traffic-manager profile list
azure network traffic-manager profile set                    az network traffic-manager profile update
azure network traffic-manager profile show                   az network traffic-manager profile show
azure network vnet create                                    az network vnet create
azure network vnet delete                                    az network vnet delete
azure network vnet list                                      az network vnet list
azure network vnet set                                       az network vnet update
azure network vnet show                                      az network vnet show
azure network vnet subnet create                             az network vnet subnet create
azure network vnet subnet delete                             az network vnet subnet delete
azure network vnet subnet list                               az network vnet subnet list
azure network vnet subnet set                                az network vnet subnet update
azure network vnet subnet show                               az network vnet subnet show
azure network vpn-connection create                          az network vpn-connection create
azure network vpn-connection delete                          az network vpn-connection delete
azure network vpn-connection list                            az network vpn-connection list
azure network vpn-connection set                             az network vpn-connection update
azure network vpn-connection shared-key reset                az network vpn-connection shared-key reset
azure network vpn-connection shared-key set                  az network vpn-connection shared-key update
azure network vpn-connection shared-key show                 az network vpn-connection shared-key show
azure network vpn-connection show                            az network vpn-connection show
azure network vpn-gateway create                             az network vpn-gateway create
azure network vpn-gateway delete                             az network vpn-gateway delete
azure network vpn-gateway list                               az network vpn-gateway list
azure network vpn-gateway revoked-cert create                az network vpn-gateway revoked-cert create
azure network vpn-gateway revoked-cert delete                az network vpn-gateway revoked-cert delete
azure network vpn-gateway root-cert create                   az network vpn-gateway root-cert create
azure network vpn-gateway root-cert delete                   az network vpn-gateway root-cert delete
azure network vpn-gateway set                                az network vpn-gateway update
azure network vpn-gateway show                               az network vpn-gateway show
azure storage account check                                  az storage account check-name
azure storage account connectionstring show                  az storage account show-connection-string
azure storage account create                                 az storage account create
azure storage account delete                                 az storage account delete
azure storage account keys list                              az storage account keys list
azure storage account keys renew                             az storage account keys renew
azure storage account list                                   az storage account list
azure storage account sas create                             az storage account generate-sas
azure storage account set                                    az storage account update
azure storage account show                                   az storage account show
azure storage account usage show                             az storage account show-usage
azure storage blob copy start                                az storage blob copy start
azure storage blob copy show                                 az storage blob show
azure storage blob copy stop                                 az storage blob copy cancel
azure storage blob delete                                    az storage blob delete
azure storage blob download                                  az storage blob download
azure storage blob lease acquire                             az storage blob lease acquire
azure storage blob lease break                               az storage blob lease break
azure storage blob lease change                              az storage blob lease change
azure storage blob lease release                             az storage blob lease release
azure storage blob lease renew                               az storage blob lease renew
azure storage blob list                                      az storage blob list
azure storage blob sas create                                az storage blob generate-sas
azure storage blob show                                      az storage blob show
azure storage blob snapshot                                  az storage blob snapshot
azure storage blob update                                    az storage blob update
azure storage blob upload                                    az storage blob upload
azure storage container create                               az storage container create
azure storage container delete                               az storage container delete
azure storage container lease acquire                        az storage container lease acquire
azure storage container lease break                          az storage container lease break
azure storage container lease change                         az storage container lease change
azure storage container lease release                        az storage container lease release
azure storage container lease renew                          az storage container lease renew
azure storage container list                                 az storage container list
azure storage container policy create                        az storage container policy create
azure storage container policy delete                        az storage container policy delete
azure storage container policy list                          az storage container policy list
azure storage container policy set                           az storage container policy update
azure storage container policy show                          az storage container policy show
azure storage container sas create                           az storage container generate-sas
azure storage container set                                  az storage container set-permission
azure storage container show                                 az storage container show
azure storage container show                                 az storage container show-permission
azure storage cors delete                                    az storage cors clear
azure storage cors set                                       az storage cors add
azure storage cors show                                      az storage cors list
azure storage directory create                               az storage directory create
azure storage directory delete                               az storage directory delete
azure storage file copy start                                az storage file copy start
azure storage file copy show                                 az storage file show
azure storage file copy stop                                 az storage file copy cancel
azure storage file delete                                    az storage file delete
azure storage file download                                  az storage file download
azure storage file list                                      az storage file list
azure storage file sas create                                az storage file generate-sas
azure storage file upload                                    az storage file upload
azure storage logging set                                    az storage logging update
azure storage logging show                                   az storage logging show
azure storage metrics set                                    az storage metrics update
azure storage metrics show                                   az storage metrics show
azure storage queue create                                   az storage queue create
azure storage queue delete                                   az storage queue delete
azure storage queue list                                     az storage queue list
azure storage queue policy create                            az storage queue policy create
azure storage queue policy delete                            az storage queue policy delete
azure storage queue policy list                              az storage queue policy list
azure storage queue policy set                               az storage queue policy update
azure storage queue policy show                              az storage queue policy show
azure storage queue sas create                               az storage queue generate-sas
azure storage queue show                                     az storage queue metadata show
azure storage share create                                   az storage share create
azure storage share delete                                   az storage share delete
azure storage share list                                     az storage share list
azure storage share policy create                            az storage share policy create
azure storage share policy delete                            az storage share policy delete
azure storage share policy list                              az storage share policy list
azure storage share policy set                               az storage share policy set
azure storage share policy show                              az storage share policy show
azure storage share sas create                               az storage share sas create
azure storage share set                                      az storage share update
azure storage share show                                     az storage share show
azure storage table create                                   az storage table create
azure storage table delete                                   az storage table delete
azure storage table list                                     az storage table list
azure storage table policy create                            az storage table policy create
azure storage table policy delete                            az storage table policy delete
azure storage table policy list                              az storage table policy list
azure storage table policy set                               az storage table policy update
azure storage table policy show                              az storage table policy show
azure storage table sas create                               az storage table generate-sas
azure vm capture                                             az vm capture
azure vm create                                              az vm create
azure vm deallocate                                          az vm deallocate
azure vm delete                                              az vm delete
azure vm disk attach                                         az vm disk attach
azure vm disk attach-new                                     az vm disk attach-new
azure vm disk detach                                         az vm disk detach
azure vm extension get                                       az vm extension get
azure vm extension set                                       az vm extension set
azure vm extension-image list                                az vm extension image list
azure vm extension-image list-types                          az vm extension image list-names
azure vm extension-image list-versions                       az vm extension image list-versions
azure vm extension-image show                                az vm extension image show
azure vm generalize                                          az vm generalize
azure vm get-instance-view                                   az vm get-instance-view
azure vm get-serial-output                                   az vm boot-diagnostics get-boot-log
azure vm image list                                          az vm image list
azure vm image list-offers                                   az vm image list-offers
azure vm image list-publishers                               az vm image list-publishers
azure vm image list-skus                                     az vm image list-skus
azure vm image show                                          az vm image show
azure vm list                                                az vm list
azure vm list-usage                                          az vm list-usage
azure vm redeploy                                            az vm redeploy
azure vm reset-access                                        az vm access
azure vm restart                                             az vm restart
azure vm set                                                 az vm update
azure vm show                                                az vm show
azure vm sizes                                               az vm list-sizes
azure vm start                                               az vm start
azure vm stop                                                az vm stop
==========================================================   ==========================================================
