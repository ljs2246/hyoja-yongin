/* Internal service IDs, NOT official administrative codes.
 * Only regions represented by the current Yongin service are selectable.
 */
(function(root){
var entries=[
 {code:'hyoja:yongin',name:'경기도 용인시',parentCode:null,gu:''},
 {code:'hyoja:yongin:cheoin',name:'경기도 용인시 처인구',parentCode:'hyoja:yongin',gu:'처인구'},
 {code:'hyoja:yongin:giheung',name:'경기도 용인시 기흥구',parentCode:'hyoja:yongin',gu:'기흥구'},
 {code:'hyoja:yongin:suji',name:'경기도 용인시 수지구',parentCode:'hyoja:yongin',gu:'수지구'}
];
if(typeof module!=='undefined'&&module.exports)module.exports=entries;
if(root)root.hjRegionCatalog=entries;
})(typeof window==='undefined'?null:window);
