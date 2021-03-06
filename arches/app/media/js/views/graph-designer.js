define([
    'jquery',
    'underscore',
    'knockout',
    'knockout-mapping',
    'views/base-manager',
    'viewmodels/alert',
    'models/graph',
    'views/graph/graph-manager/graph',
    'views/graph/graph-designer/graph-tree',
    'views/graph/graph-designer/node-form',
    'views/graph/graph-manager/branch-list',
    'views/graph/graph-designer/card-tree',
    'views/graph/permission-designer',
    'graph-designer-data',
    'arches',
    'viewmodels/graph-settings',
    'viewmodels/card',
    'view-data',
    'bindings/resizable-sidepanel',
    'datatype-config-components',
    'views/components/simple-switch'
], function($, _, ko, koMapping, BaseManagerView, AlertViewModel, GraphModel, GraphView, GraphTree, NodeFormView, BranchListView, CardTreeViewModel, PermissionDesigner, data, arches, GraphSettingsViewModel, CardViewModel, viewData) {
    var GraphDesignerView = BaseManagerView.extend({

        initialize: function(options) {
            var viewModel = options.viewModel;
            viewModel.graphid = ko.observable(data.graphid);
            viewModel.activeTab = ko.observable('graph');
            viewModel.viewState = ko.observable('design');
            viewModel.graphSettingsVisible = ko.observable(false);
            viewModel.graph = koMapping.fromJS(data['graph']);
            viewModel.ontologies = ko.observable(data['ontologies']);
            viewModel.ontologyClasses = ko.observable(data['ontologyClasses']);
            viewModel.cardComponents = data.cardComponents;

            var resources = ko.utils.arrayFilter(viewData.graphs, function(graph) {
                return graph.isresource;
            });
            var graphs = ko.utils.arrayFilter(viewData.graphs, function(graph) {
                return !graph.isresource;
            });

            viewModel.groupedGraphs = ko.observable({
                groups: [
                    { name: 'Resource Models', items: resources },
                    { name: 'Branches', items: graphs }
                ]
            });

            viewModel.graphid.subscribe(function(graphid) {
                if (graphid && graphid !== '') {
                    viewModel.navigate(arches.urls.graph_designer(graphid));
                }
            });

            viewModel.graphModel = new GraphModel({
                data: data.graph,
                datatypes: data.datatypes,
                ontology_namespaces: data.ontology_namespaces
            });

            viewModel.graphModel.on('changed', function(model, response) {
                if (viewModel.graphView) {
                    viewModel.graphView.redraw(true);
                }
                viewModel.alert(null);
                viewModel.loading(false);
                if (response.status !== 200) {
                    var errorMessageTitle = arches.requestFailed.title;
                    var errorMessageText = arches.requestFailed.text;
                    viewModel.alert(null);
                    if (response.responseJSON) {
                        errorMessageTitle = response.responseJSON.title;
                        errorMessageText = response.responseJSON.message;
                    }
                    viewModel.alert(new AlertViewModel('ep-alert-red', errorMessageTitle, errorMessageText));
                }
            });

            viewModel.graphModel.on('error', function(response) {
                viewModel.alert(new AlertViewModel('ep-alert-red', response.responseJSON.title, response.responseJSON.message));
            });

            viewModel.selectedNode = viewModel.graphModel.get('selectedNode');

            viewModel.saveNode = function(node) {
                if (node) {
                    viewModel.loading(true);
                    node.save(function(data) {
                        if (!data.responseJSON.success) {
                            viewModel.alert(new AlertViewModel('ep-alert-red', data.responseJSON.title, data.responseJSON.message));
                        }
                        viewModel.loading(false);
                    });
                }
            };

            viewModel.saveSelectedNode = function() {
                if (viewModel.selectedNode()) {
                    viewModel.saveNode(viewModel.selectedNode());
                }
            };

            viewModel.cardTree = new CardTreeViewModel({
                graph: viewModel.graph,
                graphModel: viewModel.graphModel
            });

            viewModel.nodeForm = new NodeFormView({
                graph: viewModel.graph,
                graphModel: viewModel.graphModel,
                loading: viewModel.loading,
                node: viewModel.selectedNode
            });

            viewModel.branchListView = new BranchListView({
                el: $('#branch-library'),
                branches: data.branches,
                graphModel: viewModel.graphModel,
                loading: viewModel.loading,
                disableAppendButton: ko.computed(function() {
                    // self.node() && self.node().dirty();
                })
            });

            viewModel.permissionsDesigner = new PermissionDesigner({
                cardTree: viewModel.cardTree
            });

            viewModel.graphSettingsViewModel = new GraphSettingsViewModel({
                designerViewModel: viewModel,
                graph: viewModel.graph,
                graphModel: viewModel.graphModel,
                ontologyClasses: viewModel.ontologyClasses,
                ontologies: viewModel.ontologies,
                ontologyClass: ko.observable(''),
                iconFilter: ko.observable(''),
                node: viewModel.selectedNode,
                rootNodeColor: ko.observable(''),
                ontology_namespaces: data.ontology_namespaces
            });

            viewModel.graphTree = new GraphTree({
                graphModel: viewModel.graphModel,
                graphSettings: viewModel.graphSettingsViewModel
            });

            viewModel.graphTree.branchListVisible.subscribe(function(visible) {
                if (visible) {
                    viewModel.branchListView.loadDomainConnections();
                }
            }, this);

            viewModel.loadGraphSettings = function() {
                var self = this;
                viewModel.loading(true);
                $.ajax({
                    type: 'GET',
                    url: arches.urls.new_graph_settings(data.graphid),
                    data: {'search': true, 'csrfmiddlewaretoken': '{{ csrf_token }}'}})
                    .done(function(data) {
                        self.graphSettingsViewModel.resource_data(data.resources);
                        self.graphSettingsViewModel.icon_data(data.icons);
                        self.graphSettingsViewModel.jsonCache(self.graphSettingsViewModel.jsonData());
                        self.graphSettingsViewModel.contentLoading = viewModel.loading;
                        self.graphSettingsVisible(true);
                        viewModel.loading(false);
                    })
                    .fail(function() {
                        throw 'error loading graph settings';
                    });
            };

            if (viewModel.activeTab() === 'graph') {
                viewModel.loadGraphSettings();
                // here we might load data/views asyncronously
            }

            var loadPermissionData = viewModel.activeTab.subscribe(function(tab) {
                // Loads identities and nodegroup permissions when the permissions tab is opened and then disposes the ko.subscribe.
                if (tab === 'permissions') {
                    viewModel.permissionsDesigner.getPermissionManagerData();
                    loadPermissionData.dispose();
                }
            });

            viewModel.viewState.subscribe(function(state) {
                if (state === 'preview') {
                    if (!viewModel.graphView) {
                        viewModel.graphView = new GraphView({
                            el: $('#graph'),
                            graphModel: viewModel.graphModel,
                            nodeSize: 15,
                            nodeSizeOver: 20,
                            labelOffset: 10,
                            loading: this.loading
                        });

                        viewModel.graphView.resize();

                        viewModel.graphModel.on('select-node', function(node) {
                            viewModel.graphView.zoomTo(node);
                            viewModel.graphTree.expandParentNode(node);
                        });
                    }
                }
            });


            /**
            * update the sizing of elements on window resize
            */
            var resize = function() {
                $('.grid').height($(window).height() - 208);
                $('#graph').height($(window).height() - 100);
                if (!!viewModel.graphView) {
                    viewModel.graphView.resize();
                }
            };

            $(window).resize(resize);

            resize();

            BaseManagerView.prototype.initialize.apply(this, arguments);
        }
    });

    return new GraphDesignerView();
});
